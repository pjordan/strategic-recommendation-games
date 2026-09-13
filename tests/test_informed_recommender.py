import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('game',ROOT/'analyses/scenario-1/informed-recommender/run_game.py')
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)


class InformedGameChecks(unittest.TestCase):
    def setUp(self):
        self.offers = [r for r in game.records('bing') if 10000 < r['displayed_price_cents'] < 80000][:2]
        candidates = [{'candidate_id':'empty','ordered_record_ids':[],'message':'No offer.',
                       'predicted_buyer_action':'decline','predicted_purchased_ids':[],
                       'predicted_purchase_value_cents':0,'preference_rank':3,'strategic_justification':'PRIVATE_FORECAST'}]
        for i,r in enumerate(self.offers):
            candidates.append({'candidate_id':str(i),'ordered_record_ids':[r['record_id']],
                               'message':'Consider this setup.','predicted_buyer_action':'purchase',
                               'predicted_purchased_ids':[r['record_id']],
                               'predicted_purchase_value_cents':r['displayed_price_cents'],
                               'preference_rank':i+1,'strategic_justification':'PRIVATE_FORECAST'})
        self.rec = {'selected_candidate_id':'0','candidates':candidates,'selection_reason':'PRIVATE_SELECTION','limitations':[]}
        self.response = game.materialize(self.rec,'bing')
        r = self.offers[0]
        self.buyer = {'selected_action':'purchase','selected_record_ids':[r['record_id']],
                      'purchase_value_cents':r['displayed_price_cents'],
                      'candidates':[{'candidate_id':'buy','action':'purchase','record_ids':[r['record_id']],
                                     'displayed_total_cents':r['displayed_price_cents'],'preference_rank':1,
                                     'qualification':'qualifies','evidence_and_reason':'Acceptable value.'},
                                    {'candidate_id':'decline','action':'decline','record_ids':[],
                                     'displayed_total_cents':0,'preference_rank':2,
                                     'qualification':'outside_option','evidence_and_reason':'Purchase preferred.'}],
                      'selected_outcome_reason':'Acceptable purchase.','strategic_response':'Assessed the offer.',
                      'material_assumptions':[],'limitations':[]}

    def test_exact_cards_and_private_forecast_boundary(self):
        self.assertEqual(self.response['records'],[self.offers[0]])
        prompt = game.buyer_prompt('bing',self.response)
        self.assertNotIn('PRIVATE_FORECAST',prompt)
        self.assertNotIn('PRIVATE_SELECTION',prompt)
        self.assertNotIn(self.offers[1]['record_id'],prompt)
        brief = game.adapter.scenario.load_context('buyer',version='1.2.0')['private_user_preferences']
        self.assertIn(brief,prompt)
        self.assertIn(brief,game.recommender_prompt('bing'))

    def test_recommender_cannot_predict_purchase_outside_response(self):
        bad = copy.deepcopy(self.rec)
        bad['candidates'][1]['predicted_purchased_ids']=[self.offers[1]['record_id']]
        with self.assertRaisesRegex(ValueError,'unavailable record'):
            game.validate_recommender(bad,'bing')

    def test_foreign_or_modified_records_cannot_be_returned(self):
        bad = copy.deepcopy(self.rec)
        bad['candidates'][1]['ordered_record_ids']=[game.records('google')[0]['record_id']]
        with self.assertRaisesRegex(ValueError,'unavailable record'):
            game.materialize(bad,'bing')
        bad = copy.deepcopy(self.rec)
        bad['candidates'][1]['price_override']=302
        with self.assertRaisesRegex(ValueError,'fields differ'):
            game.materialize(bad,'bing')

    def test_buyer_cannot_buy_omitted_record_or_change_price(self):
        game.validate_buyer(self.buyer,self.response)
        bad = copy.deepcopy(self.buyer);bad['selected_record_ids']=[self.offers[1]['record_id']]
        with self.assertRaisesRegex(ValueError,'unavailable record'):
            game.validate_buyer(bad,self.response)
        bad=copy.deepcopy(self.buyer);bad['purchase_value_cents']+=1
        with self.assertRaisesRegex(ValueError,'arithmetic'):
            game.validate_buyer(bad,self.response)

    def test_empty_list_requires_decline_and_zero_payoff(self):
        rec=copy.deepcopy(self.rec);rec['selected_candidate_id']='empty'
        rec['candidates'][0]['preference_rank']=1;rec['candidates'][1]['preference_rank']=2
        response=game.materialize(rec,'bing')
        buyer=copy.deepcopy(self.buyer)
        buyer.update(selected_action='decline',selected_record_ids=[],purchase_value_cents=0,candidates=[buyer['candidates'][1]])
        result=game.outcome('bing',rec,buyer,response)
        self.assertEqual(result['recommender_payoff_cents'],0)
        self.assertTrue(result['prediction_matched'])

    def test_subsets_allowed_but_overbudget_purchase_rejected(self):
        response=copy.deepcopy(self.response);response['records'].append(self.offers[1])
        game.validate_buyer(self.buyer,response)
        costly=next(r for r in game.records('bing') if r['displayed_price_cents']>80000)
        with self.assertRaisesRegex(ValueError,'budget'):
            game.check_purchase('purchase',[costly['record_id']],costly['displayed_price_cents'],{costly['record_id']:costly})

    def test_recommender_selection_and_buyer_selection_match_rankings(self):
        bad=copy.deepcopy(self.rec);bad['selected_candidate_id']='empty'
        with self.assertRaisesRegex(ValueError,'ranking'):
            game.validate_recommender(bad,'bing')
        bad=copy.deepcopy(self.buyer);bad['candidates'][0]['preference_rank']=3
        with self.assertRaisesRegex(ValueError,'ranking'):
            game.validate_buyer(bad,self.response)


if __name__ == '__main__':
    unittest.main()
