import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('two_round_game',ROOT/'analyses/scenario-1/two-round-strategic-disclosure/run_game.py')
game=importlib.util.module_from_spec(spec);spec.loader.exec_module(game)


def plan(followup=False):
    cs=[]
    for i in range(3):
        c={'candidate_id':str(i),'messages':{p:p.upper()+'_MESSAGE_'+str(i) for p in ('bing','google')},
           'preference_rank':i+1,'disclosure_and_withholding':'PLAN_PRIVATE',
           'anticipated_recommender_behavior':'FORECAST_PRIVATE','expected_user_value_tradeoff':'VALUE_PRIVATE'}
        if followup:c['shared_record_ids']={p:[] for p in ('bing','google')}
        cs.append(c)
    return {'selected_candidate_id':'0','candidates':cs,'selection_reason':'SELECTED_REASON','limitations':[]}


def rec(provider):
    r=game.records(provider)[0]
    cs=[]
    for i in range(3):
        cs.append({'candidate_id':str(i),'ordered_record_ids':[r['record_id']] if i<2 else [],
                   'message':provider.upper()+'_REPLY_'+str(i),'preference_rank':i+1,
                   'strategic_justification':'OWN_PRIVATE_STRATEGY',
                   'predicted_buyer_choice':'own_provider' if i<2 else 'decline',
                   'predicted_own_purchased_ids':[r['record_id']] if i<2 else [],
                   'predicted_own_revenue_cents':r['displayed_price_cents'] if i<2 else 0})
    return {'selected_candidate_id':'0','candidates':cs,'selection_reason':'OWN_PRIVATE_REASON',
            'buyer_belief':'OWN_PRIVATE_BELIEF','limitations':[]}


class TwoRoundChecks(unittest.TestCase):
    def setUp(self):
        self.d=plan();self.f=plan(True)
        self.recs={p:rec(p) for p in ('bing','google')}
        self.rs={p:game.materialize(self.recs[p],p) for p in ('bing','google')}

    def test_early_buyer_and_recommender_boundaries(self):
        with patch.object(game,'private_context',return_value='SECRET_TRUE_BRIEF $800'):
            self.assertIn('SECRET_TRUE_BRIEF',game.disclosure_prompt())
            for p,q in [('bing','google'),('google','bing')]:
                prompt=game.recommender_prompt(p,self.d['candidates'][0]['messages'][p])
                self.assertNotIn('SECRET_TRUE_BRIEF',prompt)
                self.assertNotIn('$800',prompt.split('## Complete frozen own-provider catalog')[0])
                self.assertNotIn(q.upper()+'_MESSAGE',prompt)
                self.assertNotIn(game.records(q)[0]['record_id'],prompt)
                self.assertNotIn(game.records(p)[0]['record_id'],game.disclosure_prompt())

    def test_followup_gets_both_first_replies_but_no_unselected_actions(self):
        prompt=game.followup_prompt(self.rs,self.d)
        for p in ('bing','google'):
            self.assertIn(p.upper()+'_REPLY_0',prompt)
            self.assertIn(p.upper()+'_MESSAGE_0',prompt)
            self.assertNotIn(p.upper()+'_REPLY_1',prompt)
            self.assertNotIn(p.upper()+'_MESSAGE_1',prompt)
        self.assertIn(game.private_context(),prompt)
        self.assertNotIn('OWN_PRIVATE_BELIEF',prompt)

    def test_followup_evidence_must_be_observed_and_unmodified(self):
        g=self.rs['google']['records'][0]
        self.f['candidates'][0]['shared_record_ids']['bing']=[g['record_id']]
        forwarded=game.followups(self.f,self.rs)
        self.assertEqual(forwarded['bing']['shared_records'],[g])
        self.assertEqual(forwarded['google']['shared_records'],[])
        bad=copy.deepcopy(self.f)
        bad['candidates'][0]['shared_record_ids']['bing']=[game.records('google')[1]['record_id']]
        with self.assertRaisesRegex(ValueError,'unavailable'):
            game.followups(bad,self.rs)
        bad_rs=copy.deepcopy(self.rs);bad_rs['google']['records'][0]['displayed_price_cents']=1
        with self.assertRaisesRegex(ValueError,'modified'):
            game.followups(self.f,bad_rs)

    def test_second_provider_only_own_history_and_deliberately_shared_evidence(self):
        g=self.rs['google']['records'][0]
        self.f['candidates'][0]['shared_record_ids']['bing']=[g['record_id']]
        forward=game.followups(self.f,self.rs)
        with patch.object(game,'private_context',return_value='SECRET_TRUE_BRIEF $800'):
            prompt=game.second_recommender_prompt('bing','INITIAL_BING',self.recs['bing'],forward['bing'])
        self.assertIn(g['record_id'],prompt)
        self.assertIn('BING_MESSAGE_0',prompt)
        self.assertIn('BING_REPLY_0',prompt)
        self.assertIn('OWN_PRIVATE_BELIEF',prompt)
        for excluded in ['GOOGLE_MESSAGE_0','GOOGLE_REPLY_0','BING_REPLY_1','SECRET_TRUE_BRIEF',game.records('google')[1]['record_id']]:
            self.assertNotIn(excluded,prompt)

    def test_round_one_offer_survives_empty_second_reply_and_is_credited_once(self):
        empty={p:{'provider':p,'message':'No new offers','records':[]} for p in ('bing','google')}
        merged=game.combine_responses([self.rs,empty])
        self.assertEqual(merged['records'],game.combine_responses([self.rs,self.rs])['records'])
        r=self.rs['bing']['records'][0]
        second=copy.deepcopy(self.recs)
        for p in ('bing','google'):
            second[p]['selected_candidate_id']='2'
            second[p]['candidates'][2]['preference_rank']=1
            second[p]['candidates'][0]['preference_rank']=2
        c=second['bing']['candidates'][2]
        c.update(predicted_buyer_choice='own_provider',predicted_own_purchased_ids=[r['record_id']],predicted_own_revenue_cents=r['displayed_price_cents'])
        # A round-2 empty response can forecast purchase of its persistent round-1 offer.
        game.validate_recommender(second['bing'],'bing',self.rs['bing'])
        with self.assertRaisesRegex(ValueError,'unavailable'):
            game.validate_recommender(second['bing'],'bing')
        rs2={p:game.materialize(second[p],p,self.rs[p]) for p in ('bing','google')}
        buyer={'selected_action':'purchase','selected_record_ids':[r['record_id']],'purchase_value_cents':r['displayed_price_cents'],
               'candidates':[{'candidate_id':'buy','action':'purchase','record_ids':[r['record_id']],
                              'displayed_total_cents':r['displayed_price_cents'],'preference_rank':1,'qualification':'qualifies','evidence_and_reason':'Value.'},
                             {'candidate_id':'decline','action':'decline','record_ids':[],'displayed_total_cents':0,
                              'preference_rank':2,'qualification':'outside_option','evidence_and_reason':'No purchase.'}],
               'selected_outcome_reason':'Value','strategic_response':'Reason','material_assumptions':[],'limitations':[]}
        result=game.outcome([self.recs,second],buyer,[self.rs,rs2],self.d,self.f)
        self.assertEqual(result['recommenders']['bing']['realized_own_revenue_cents'],r['displayed_price_cents'])
        self.assertEqual(result['selected_records_first_available_round'],{r['record_id']:1})
        self.assertEqual(result['unique_returned_count'],2)

    def test_final_buyer_sees_both_rounds_and_true_preferences(self):
        rs2=copy.deepcopy(self.rs)
        for p in rs2:rs2[p]['message']='SECOND_'+p
        prompt=game.buyer_prompt([self.rs,rs2],self.d,self.f)
        self.assertIn(game.private_context(),prompt)
        for p in rs2:
            self.assertIn(p.upper()+'_REPLY_0',prompt)
            self.assertIn('SECOND_'+p,prompt)
        self.assertNotIn('OWN_PRIVATE_BELIEF',prompt)
        self.assertNotIn('BING_MESSAGE_1',prompt)
        with self.assertRaisesRegex(ValueError,'both rounds'):
            game.buyer_prompt([self.rs],self.d,self.f)

    def test_shared_rival_offer_cannot_be_returned_for_own_credit(self):
        bad=copy.deepcopy(self.recs['bing'])
        bad['candidates'][0]['ordered_record_ids']=[self.rs['google']['records'][0]['record_id']]
        with self.assertRaisesRegex(ValueError,'unavailable'):
            game.materialize(bad,'bing',self.rs['bing'])


if __name__=='__main__':unittest.main()
