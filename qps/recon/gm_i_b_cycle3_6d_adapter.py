#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, os
from datetime import UTC, datetime
from pathlib import Path

OUT = Path('qps/recon/GM_I_B_CYCLE3_TEMPORAL_PCA_6D_ADAPTER_RECEIPT_v1.json')
EXPECTED_FEATURES = [
    {"name":"T_K","unit":"K"},
    {"name":"p_Pa","unit":"Pa"},
    {"name":"h_J_kg","unit":"J/kg"},
    {"name":"s_J_kgK","unit":"J/(kg*K)"},
    {"name":"rho_kg_m3","unit":"kg/m^3"},
    {"name":"cp_J_kgK","unit":"J/(kg*K)"}
]

def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",",":")).encode()).hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--contract',type=Path,required=True); p.add_argument('--atom',type=Path,required=True); p.add_argument('--crosswalk',type=Path,required=True); a=p.parse_args()
    c=json.loads(a.contract.read_text()); atom=json.loads(a.atom.read_text()); x=json.loads(a.crosswalk.read_text())
    targets={t['id']:t for t in c['propagation_targets']}; t=targets['T2_COOLPROP']; semantic=c['semantic_invariants']
    rows=[]; state_order=['A','B','D','E','W']
    for sid in state_order:
        s=x['states'][sid]
        vals=[s['T_K'],s['P_Pa'],s['h_J_kg'],s['s_J_kgK'],s['rho_kg_m3'],s['cp_J_kgK']]
        rows.append({'state_id':sid,'vector':[float(v) for v in vals],'finite':all(math.isfinite(float(v)) for v in vals)})
    checks={
      'contract_merge_pinned': c['refresh_state']['missioncontrol_master']=='7af02c89ca640c180b20341e0016c5f82096da26' and c['source_atom']['keb_item_id']=='KEB-ITEM-0002',
      'atom_exact': atom['keb_item_id']=='KEB-ITEM-0002' and atom['source_digest']==c['source_atom']['source_digest'],
      'target_role': t['repo']=='GBOGEB/CoolProp' and t['role']=='TYPED_THERMOPHYSICAL_DOMAIN_FEATURE_ADAPTER',
      'dimension_6': t['required_feature_dimension']==6,
      'feature_schema_exact': t['required_feature_schema']==EXPECTED_FEATURES,
      'crosswalk_reused': x['schema']=='qps-coolprop-w145-lkt-2kop-crosswalk/0.1' and x['summary']['status']=='PASS' and x['summary']['states_passed']==5,
      'five_rows': len(rows)==5 and [r['state_id'] for r in rows]==state_order,
      'all_finite': all(r['finite'] for r in rows),
      'no_pca_reimplementation': t['new_independent_math_implementation_allowed'] is False and c['generalisation_rules']['consumer_may_implement_duplicate_pca_kernel'] is False,
      'semantic_parity': len(semantic)==6 and semantic['component_assignment_precedes_sign_alignment'] is True and semantic['raw_pca_loading_sign_is_not_physical_direction'] is True and semantic['attenuation_toward_parity_is_distinct_from_direction_reversal'] is True and semantic['small_eigengap_requires_subspace_context'] is True and semantic['temporal_state_adjacency_does_not_require_equal_wall_time_or_exposure_age_steps'] is True and semantic['named_clocks']==['k','t','a','wave','pulse','pr','run','release'],
      'authority_boundary': atom['authority_guards']['authority_transfer'] is False and x['authority']['engineering_promotion_forbidden'] is True
    }
    ok=all(checks.values())
    out={
      'schema':'coolprop.gm_i_b.3p_ral_cycle3_6d_domain_adapter_receipt.v1',
      'created_utc':datetime.now(UTC).replace(microsecond=0).isoformat(),
      'status':'ACCEPT_SCHEMA_ADAPTER_ONLY' if ok else 'DEFER_SCHEMA_ADAPTER',
      'consumer':'GBOGEB/CoolProp',
      'source_head':os.environ.get('GITHUB_SHA','LOCAL_UNBOUND'),
      'missioncontrol_contract_merge':'3348189fd52883befb24f5c5b6bb3953cd8725ab',
      'source_atom':{'keb_item_id':atom['keb_item_id'],'source_digest':atom['source_digest'],'authority_cap':atom['authority_cap']},
      'feature_dimension':6,
      'feature_schema':EXPECTED_FEATURES,
      'state_order':state_order,
      'feature_matrix':[r['vector'] for r in rows],
      'row_receipts':rows,
      'semantic_invariants':semantic,
      'checks':checks,
      'generalisation':{
        'domain_adapter_only':True,
        'computes_pca':False,
        'imports_gg_MATH':False,
        'imports_ABACUS_temporal_PCA':False,
        'duplicate_implementation_count':0,
        'feature_dimension_is_not_display_dimension':True,
        'schema_mapping_is_pca_result':False
      },
      'kpi':{
        'propagation_targets_total':3,
        'propagation_targets_reached':2 if ok else 1,
        'propagation_coverage':(2/3) if ok else (1/3),
        'semantic_invariants_total':6,
        'semantic_invariants_preserved':6 if ok else 0,
        'semantic_parity':1.0 if ok else 0.0,
        'reuse_ratio':1.0 if ok else 0.0,
        'duplicate_implementation_count':0,
        'child_disposition_coverage':0.5 if ok else 0.0,
        'propagation_depth_from_keb_atom':2 if ok else 1,
        'authority_inversion_count':0
      },
      'authority_transfer':False,
      'formal_credit_delta':0,
      'engineering_authority_created':False,
      'next_action':'PROPAGATE_TO_T3_QPS_TRIAGE' if ok else 'REPAIR_FIRST_RED'
    }
    out['contract_sha256']=digest(c); out['atom_sha256']=digest(atom); out['crosswalk_sha256']=digest(x); out['receipt_sha256']=digest(out)
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
