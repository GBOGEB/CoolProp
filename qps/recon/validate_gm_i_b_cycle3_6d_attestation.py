#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path

FEATURES=[('T_K','K'),('p_Pa','Pa'),('h_J_kg','J/kg'),('s_J_kgK','J/(kg*K)'),('rho_kg_m3','kg/m^3'),('cp_J_kgK','J/(kg*K)')]
CLOCKS=['k','t','a','wave','pulse','pr','run','release']

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--attestation',type=Path,required=True); p.add_argument('--contract',type=Path,required=True); p.add_argument('--atom',type=Path,required=True); a=p.parse_args()
    r=json.loads(a.attestation.read_text()); c=json.loads(a.contract.read_text()); atom=json.loads(a.atom.read_text())
    matrix=r['feature_matrix']; sem=r['semantic_invariants']; g=r['generalisation']; k=r['kpi']
    checks={
      'status': r['status']=='ACCEPT_SCHEMA_ADAPTER_ONLY',
      'mission': r['mission']=='GM-I-B' and r['cycle']==3 and r['child_target']=='T2_COOLPROP',
      'contract': r['missioncontrol_contract']['merge_sha']=='3348189fd52883befb24f5c5b6bb3953cd8725ab' and c['source_atom']['keb_item_id']=='KEB-ITEM-0002',
      'atom': r['source_atom']['keb_item_id']==atom['keb_item_id']=='KEB-ITEM-0002' and r['source_atom']['source_digest']==atom['source_digest'],
      'transaction': r['coolprop_transaction']['tested_exact_head']=='b2f6fc4e8760c3d6fe608f6673e4a4155e116233' and r['coolprop_transaction']['merge_sha']=='6f4905a95ed90dafe72f2b237df91896f540b7f4' and r['coolprop_transaction']['workflow_run']==35154983524 and r['coolprop_transaction']['workflow_job']==104992179225 and r['coolprop_transaction']['workflow_result']=='SUCCESS' and r['coolprop_transaction']['workflow_steps_gt_zero'] is True and r['coolprop_transaction']['artifact_id']==10471025052 and r['coolprop_transaction']['artifact_sha256']=='05d3f026408a079038612b23191efcee14e2f2db03481dc3012f00d835b13a07' and r['coolprop_transaction']['runtime_receipt_sha256']=='713e4ba99bd1aff7240e4f1e02956d45073ace20ac09c05d7cd9af310a4796b8',
      'schema': r['feature_dimension']==6 and [(x['name'],x['unit']) for x in r['feature_schema']]==FEATURES,
      'matrix': len(matrix)==5 and all(len(row)==6 and all(math.isfinite(float(v)) for v in row) for row in matrix) and r['state_order']==['A','B','D','E','W'],
      'semantics': len(sem)==6 and sem['named_clocks']==CLOCKS and sem['component_assignment_precedes_sign_alignment'] is True and sem['raw_pca_loading_sign_is_not_physical_direction'] is True and sem['attenuation_toward_parity_is_distinct_from_direction_reversal'] is True and sem['small_eigengap_requires_subspace_context'] is True and sem['temporal_state_adjacency_does_not_require_equal_wall_time_or_exposure_age_steps'] is True,
      'reuse_only': g['domain_adapter_only'] is True and g['computes_pca'] is False and g['imports_gg_MATH'] is False and g['imports_ABACUS_temporal_PCA'] is False and g['duplicate_implementation_count']==0 and g['schema_mapping_is_pca_result'] is False,
      'kpis': k['propagation_targets_total']==3 and k['propagation_targets_reached']==2 and abs(k['propagation_coverage']-2/3)<1e-12 and k['semantic_parity']==1.0 and k['reuse_ratio']==1.0 and k['duplicate_implementation_count']==0 and k['child_targets_total']==2 and k['child_dispositions_observed']==1 and k['child_disposition_coverage']==0.5 and k['propagation_depth_from_keb_atom']==2 and k['authority_inversion_count']==0,
      'authority': r['authority_transfer'] is False and r['formal_credit_delta']==0 and r['engineering_authority_created'] is False and r['hard_gate_compensation_allowed'] is False
    }
    print(json.dumps({'status':'PASS_COOLPROP_POSTPROOF_ATTESTATION' if all(checks.values()) else 'DEFER','checks':checks},indent=2,sort_keys=True))
    return 0 if all(checks.values()) else 1
if __name__=='__main__': raise SystemExit(main())
