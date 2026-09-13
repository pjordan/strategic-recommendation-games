import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('disclosure_game',ROOT/'analyses/scenario-1/strategic-disclosure/run_game.py')
game=importlib.util.module_from_spec(spec);spec.loader.exec_module(game)


class DisclosureChecks(unittest.TestCase):
    def setUp(self):
        cs=[]
        for i in range(3):
            cs.append({'candidate_id':str(i),'messages':{'bing':'BING_ONLY_'+str(i),'google':'GOOGLE_ONLY_'+str(i)},
                       'preference_rank':i+1,'disclosure_and_withholding':'PLAN_PRIVATE',
                       'anticipated_recommender_behavior':'FORECAST_PRIVATE','expected_user_value_tradeoff':'USER_VALUE'})
        self.disclosure={'selected_candidate_id':'0','candidates':cs,'selection_reason':'SELECTED_REASON','limitations':[]}
        self.responses={p:{'provider':p,'message':'Response from '+p,'records':[game.records(p)[0]]} for p in ('bing','google')}

    def test_recommender_receives_only_own_message_no_brief_or_rival_catalog(self):
        with patch.object(game,'private_context',return_value='SECRET_TRUE_BRIEF budget $800'):
            for provider,other in [('bing','google'),('google','bing')]:
                prompt=game.recommender_prompt(provider,self.disclosure['candidates'][0]['messages'][provider])
                preamble=prompt.split('## Complete frozen own-provider catalog')[0]
                self.assertNotIn('SECRET_TRUE_BRIEF',prompt)
                self.assertNotIn('$800',preamble)
                self.assertNotIn('80000',preamble)
                self.assertIn(provider.upper()+'_ONLY_0',prompt)
                self.assertNotIn(other.upper()+'_ONLY_0',prompt)
                self.assertNotIn('PLAN_PRIVATE',prompt)
                self.assertNotIn('FORECAST_PRIVATE',prompt)
                self.assertNotIn(game.records(other)[0]['record_id'],prompt)

    def test_disclosure_stage_has_preferences_but_no_catalog(self):
        prompt=game.disclosure_prompt()
        self.assertIn(game.private_context(),prompt)
        for provider in ('bing','google'):
            self.assertNotIn(game.records(provider)[0]['record_id'],prompt)

    def test_final_buyer_gets_true_preferences_and_selected_state_only(self):
        with patch.object(game,'private_context',return_value='SECRET_TRUE_BRIEF budget $800'):
            prompt=game.buyer_prompt(self.responses,self.disclosure)
            self.assertIn('SECRET_TRUE_BRIEF',prompt)
            self.assertIn('BING_ONLY_0',prompt);self.assertIn('GOOGLE_ONLY_0',prompt)
            self.assertIn('SELECTED_REASON',prompt)
            self.assertNotIn('BING_ONLY_1',prompt);self.assertNotIn('GOOGLE_ONLY_2',prompt)
            for p in ('bing','google'):
                self.assertIn(game.records(p)[0]['record_id'],prompt)

    def test_disclosure_must_match_rank_and_have_two_addressed_messages(self):
        bad=copy.deepcopy(self.disclosure);bad['selected_candidate_id']='2'
        with self.assertRaisesRegex(ValueError,'ranking'):
            game.validate_disclosure(bad)
        bad=copy.deepcopy(self.disclosure);bad['candidates'][0]['messages'].pop('google')
        with self.assertRaisesRegex(ValueError,'fields differ'):
            game.validate_disclosure(bad)

    def test_forecast_does_not_reveal_hidden_budget_but_actual_purchase_checks_it(self):
        offers=[r for r in game.records('bing') if r['displayed_price_cents']>80000][:2]
        candidates=[{'candidate_id':'empty','ordered_record_ids':[],'message':'No offer.',
                     'preference_rank':3,'strategic_justification':'Uncertain buyer.',
                     'predicted_buyer_choice':'other_provider','predicted_own_purchased_ids':[],
                     'predicted_own_revenue_cents':0}]
        for i,r in enumerate(offers):
            candidates.append({'candidate_id':str(i),'ordered_record_ids':[r['record_id']],'message':'Offer.',
                               'preference_rank':i+1,'strategic_justification':'Belief about willingness to pay.',
                               'predicted_buyer_choice':'own_provider','predicted_own_purchased_ids':[r['record_id']],
                               'predicted_own_revenue_cents':r['displayed_price_cents']})
        rec={'selected_candidate_id':'0','candidates':candidates,'selection_reason':'Expected revenue.',
             'buyer_belief':'Budget unknown.','limitations':[]}
        game.validate_recommender(rec,'bing')
        response=game.materialize(rec,'bing');r=offers[0]
        with self.assertRaisesRegex(ValueError,'budget'):
            game.check_purchase('purchase',[r['record_id']],r['displayed_price_cents'],{r['record_id']:r})
        self.assertEqual(response['records'],[r])
        self.assertNotIn('buyer_belief',response)


if __name__=='__main__':
    unittest.main()
