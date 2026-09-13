import copy
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('competition',ROOT/'analyses/scenario-1/competing-recommenders/run_game.py')
game=importlib.util.module_from_spec(spec);spec.loader.exec_module(game)


class CompetitionChecks(unittest.TestCase):
    def setUp(self):
        self.offers={p:[r for r in game.records(p) if 10000<r['displayed_price_cents']<30000][:2] for p in ('bing','google')}
        self.recs={}
        for p in ('bing','google'):
            cs=[{'candidate_id':'empty','ordered_record_ids':[],'message':'No offers.',
                 'predicted_buyer_choice':'other_provider','predicted_own_purchased_ids':[],
                 'predicted_own_revenue_cents':0,'preference_rank':3,'strategic_justification':'SECRET_FORECAST'}]
            for i,r in enumerate(self.offers[p]):
                cs.append({'candidate_id':str(i),'ordered_record_ids':[r['record_id']],'message':'Consider this offer.',
                           'predicted_buyer_choice':'own_provider','predicted_own_purchased_ids':[r['record_id']],
                           'predicted_own_revenue_cents':r['displayed_price_cents'],'preference_rank':i+1,
                           'strategic_justification':'SECRET_FORECAST'})
            self.recs[p]={'selected_candidate_id':'0','candidates':cs,'selection_reason':'SECRET_SELECTION','limitations':[]}
        self.responses={p:game.materialize(self.recs[p],p) for p in ('bing','google')}

    def buyer(self,ids):
        catalog={r['record_id']:r for r in game.combine_responses(self.responses)['records']}
        price=sum(catalog[i]['displayed_price_cents'] for i in ids)
        decline={'candidate_id':'decline','action':'decline','record_ids':[], 'displayed_total_cents':0,
                 'preference_rank':2 if ids else 1,'qualification':'outside_option','evidence_and_reason':'Outside option.'}
        purchase_ids=ids or [self.offers['bing'][0]['record_id']]
        purchase={'candidate_id':'buy','action':'purchase','record_ids':purchase_ids,
                  'displayed_total_cents':sum(catalog[i]['displayed_price_cents'] for i in purchase_ids),
                  'preference_rank':1 if ids else 2,'qualification':'qualifies','evidence_and_reason':'Satisfying bundle.'}
        return {'selected_action':'purchase' if ids else 'decline','selected_record_ids':ids,'purchase_value_cents':price,
                'candidates':[purchase,decline],'selected_outcome_reason':'Selected preference.',
                'strategic_response':'Compared both lists.','material_assumptions':[],'limitations':[]}

    def test_buyer_sees_both_lists_but_no_private_forecasts(self):
        prompt=game.buyer_prompt(self.responses)
        for p in ('bing','google'):
            self.assertIn(self.offers[p][0]['record_id'],prompt)
            self.assertNotIn(self.offers[p][1]['record_id'],prompt)
        self.assertNotIn('SECRET_FORECAST',prompt);self.assertNotIn('SECRET_SELECTION',prompt)
        with self.assertRaisesRegex(ValueError,'both committed'):
            game.buyer_prompt({'bing':self.responses['bing']})

    def test_recommenders_do_not_see_rival_catalog_or_response(self):
        for p,other in [('bing','google'),('google','bing')]:
            prompt=game.recommender_prompt(p)
            self.assertIn(self.offers[p][0]['record_id'],prompt)
            self.assertNotIn(self.offers[other][0]['record_id'],prompt)
            self.assertNotIn('SECRET_SELECTION',prompt)
            self.assertIn('complete user',prompt.lower().replace('full user','complete user'))

    def test_display_order_changes_blocks_only(self):
        first=game.combine_responses(self.responses,'bing-first')['records']
        second=game.combine_responses(self.responses,'google-first')['records']
        self.assertEqual(first,list(reversed(second)))
        self.assertEqual(set(map(lambda r:r['record_id'],first)),set(map(lambda r:r['record_id'],second)))

    def test_single_winner_earns_only_own_revenue(self):
        for p,other in [('bing','google'),('google','bing')]:
            r=self.offers[p][0]; result=game.outcome(self.recs,self.buyer([r['record_id']]),self.responses)
            self.assertEqual(result['recommenders'][p]['realized_own_revenue_cents'],r['displayed_price_cents'])
            self.assertEqual(result['recommenders'][other]['realized_own_revenue_cents'],0)
            self.assertEqual(result['recommenders'][other]['actual_buyer_choice'],'other_provider')

    def test_cross_provider_bundle_revenue_conservation(self):
        ids=[self.offers[p][0]['record_id'] for p in ('bing','google')]
        result=game.outcome(self.recs,self.buyer(ids),self.responses)
        self.assertEqual(sum(r['realized_own_revenue_cents'] for r in result['recommenders'].values()),result['purchase_value_cents'])
        self.assertEqual(result['credited_providers'],['bing','google'])
        self.assertTrue(all(r['actual_buyer_choice']=='mixed_bundle' for r in result['recommenders'].values()))

    def test_decline_pays_neither_provider(self):
        result=game.outcome(self.recs,self.buyer([]),self.responses)
        self.assertEqual(result['purchase_value_cents'],0)
        self.assertEqual(result['credited_providers'],[])

    def test_modified_foreign_and_omitted_records_rejected(self):
        bad=copy.deepcopy(self.responses);bad['bing']['records'][0]['displayed_price_cents']+=1
        with self.assertRaisesRegex(ValueError,'modified'):
            game.combine_responses(bad)
        bad=copy.deepcopy(self.responses);bad['bing']['records']=[self.offers['google'][0]]
        with self.assertRaisesRegex(ValueError,'unavailable'):
            game.combine_responses(bad)
        b=self.buyer([self.offers['bing'][0]['record_id']]);b['selected_record_ids']=[self.offers['bing'][1]['record_id']]
        with self.assertRaisesRegex(ValueError,'unavailable'):
            game.outcome(self.recs,b,self.responses)

    def test_invalid_lower_ranked_id_rejected_even_when_selection_is_valid(self):
        ids=[self.offers['bing'][0]['record_id']]
        buyer=self.buyer(ids)
        alternative=copy.deepcopy(buyer['candidates'][0])
        alternative.update(candidate_id='bad_alternative',preference_rank=3,
                           record_ids=[self.offers['google'][0]['record_id']+'e'])
        buyer['candidates'].append(alternative)
        with self.assertRaisesRegex(ValueError,'unavailable'):
            game.outcome(self.recs,buyer,self.responses)

    def test_rival_win_forecast_cannot_claim_own_revenue(self):
        bad=copy.deepcopy(self.recs['bing']);bad['candidates'][1]['predicted_buyer_choice']='other_provider'
        with self.assertRaisesRegex(ValueError,'Decline requires'):
            game.validate_recommender(bad,'bing')


if __name__=='__main__':
    unittest.main()
