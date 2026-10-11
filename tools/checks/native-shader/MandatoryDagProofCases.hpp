#pragma once
#include "RdnaDecoder/RdnaProgram.hpp"
#include "ControlFlow/ControlFlowGraph.hpp"
#include <functional>
#include <string>
#include <vector>
// Synthetic encodings only. This file contains no serialized game request.
namespace PublicMandatoryDagProofCases {
using namespace ShaderRecompiler;
using Code=std::vector<std::uint32_t>;
using Change=std::function<void(RdnaProgram&,ControlFlowGraph&)>;
struct Case {std::string name;Code code;bool expected;Change change{};std::string decodeRejection{};};
inline Code synthetic(Code arm={0x7e0c0304u,0xbf8c0070u}) {
 Code code={0xc8100000u,0xc8110001u,0xbf870000u|static_cast<unsigned>(arm.size())};
 code.insert(code.end(),arm.begin(),arm.end());
 const Code rest={0xc8140000u,0xc8150001u,0xbf850002u,0x7e0e0305u,0xbf8c0070u,
                  0xc8180000u,0xc8190001u,0x7e000280u,0x7e020280u,0xf800180fu,0x06060505u,0xbf810000u};
 code.insert(code.end(),rest.begin(),rest.end());return code;
}
inline std::vector<Case> cases() {
 std::vector<Case> all;
 const auto add=[&](std::string name,Code code,bool expected,Change change={}){
  all.push_back({"mandatory_dag_"+name,std::move(code),expected,std::move(change)});
 };
 auto c=synthetic();add("two_forward_optional_regions",c,true);
 auto scc=c;scc[2]=0xbf840002u;add("SCC_zero_optional_region",scc,true);
 auto vcc=c;vcc[2]=0xbf860002u;vcc[7]=0xbf870002u;add("VCC_zero_and_nonzero_regions",vcc,true);
 auto consume=c;consume[10]=0xc8000000u;consume[11]=0xc8010001u;add("terminal_complete_pair_consumes_I_in_place",consume,true);
 auto readI=c;readI[3]=0x7e0c0300u;add("optional_raw_I_read",readI,false);
 auto readJ=c;readJ[3]=0x7e0c0301u;add("optional_raw_J_read",readJ,false);
 auto writeI=c;writeI[3]=0x7e000304u;add("optional_raw_I_write",writeI,false);
 auto writeJ=c;writeJ[4]=0x7e020304u;add("nonterminal_last_instruction_raw_J_write",writeJ,false);
 auto kill=c;kill[3]=0x7e000304u;kill[4]=0x7e0c0300u;add("optional_overwrite_then_read_raw_I",kill,false);
 auto exec=c;exec[3]=0xbefe0380u;add("optional_EXEC_write",exec,false);
 auto m0=c;m0[3]=0xbefc0380u;add("optional_M0_write",m0,false);
 auto middleM0=c;middleM0[8]=0xbefc0380u;add("later_optional_M0_write",middleM0,false);
 auto pending=c;pending[1]=0xbf8c0070u;add("entry_partial_pair_crosses_branch",pending,false);
 auto cross=c;cross[6]=0xbf8c0070u;add("middle_partial_pair_crosses_branch",cross,false);
 auto optional=synthetic({0xc8240000u,0xc8250001u});add("complete_pair_on_only_one_arm",optional,false);
 auto bypass=c;bypass[2]=0xbf870007u;add("branch_bypasses_middle_interpolation",bypass,false);
 auto terminalM0=c;terminalM0.insert(terminalM0.begin()+10,0xbefc0380u);add("terminal_M0_changes_later_pair_base",terminalM0,false);
 auto terminalExec=c;terminalExec.insert(terminalExec.begin()+10,0xbefe0380u);add("terminal_EXEC_change_before_last_pair",terminalExec,false);
 auto late=c;late.insert(late.end()-1,{0xc8100000u,0xc8110001u});add("later_pair_after_terminal_raw_consumption",late,false);
 auto copy=c;copy[5]=0xc8140002u;copy[6]=0xc8150003u;add("copied_IJ_pair_not_original",copy,false);
 auto indexed=c;indexed[3]=0x7e0c8904u;add("indexed_vector_effect_not_admitted",indexed,false);
 auto unknown=c;unknown[3]=0xbf8a0000u;add("optional_barrier_not_admitted",unknown,false);
 auto backward=c;backward[2]=0xbf87ffffu;add("conditional_backedge_not_admitted",backward,false);
 auto execBranch=c;execBranch[2]=0xbf880002u;add("EXEC_condition_not_admitted",execBranch,false);
 // Explicit-LOD cube-like address uses base v21 plus active NSA v6/v7/v9;
 // the fourth encoded byte and all twelve-array padding zeros are unused.
 Code nsa={0xf0900f1au,0x00c20a15u,0x00090706u};
 auto nsaCode=synthetic(nsa);add("NSA_inactive_zero_bytes_and_padding",nsaCode,true);
 auto activeI=nsa;activeI[2]&=0xffffff00u;add("NSA_active_raw_I_read",synthetic(activeI),false);
 auto activeJ=nsa;activeJ[2]=(activeJ[2]&0xffff00ffu)|0x00000100u;add("NSA_active_raw_J_read",synthetic(activeJ),false);
 auto inactiveJ=nsa;inactiveJ[2]|=0x01000000u;add("NSA_inactive_encoded_raw_J_byte",synthetic(inactiveJ),true);
 auto destinationJ=nsa;destinationJ[1]=(destinationJ[1]&0xffff00ffu)|0x00000100u;add("NSA_destination_overlaps_raw_J",synthetic(destinationJ),false);
 auto tfe=nsa;tfe[0]|=0x10000u;add("NSA_TFE_status_not_admitted",synthetic(tfe),false);
 auto rawAddress=nsa;rawAddress[1]&=0xffffff00u;add("NSA_base_raw_I_read",synthetic(rawAddress),false);
 auto a16=nsa;a16[1]|=0x40000000u;add("NSA_A16_packed_address_not_admitted",synthetic(a16),false);
 auto d16=nsa;d16[1]|=0x80000000u;add("NSA_D16_packed_result_not_admitted",synthetic(d16),false);
 auto r128=nsa;r128[0]|=0x8000u;add("NSA_R128_descriptor_not_admitted",synthetic(r128),false);
 auto bias=nsa;bias[0]=(bias[0]&~(0x7fu<<18u))|(0x25u<<18u);add("NSA_bias_sampling_not_admitted",synthetic(bias),false);
 auto lz=nsa;lz[0]=(lz[0]&~(0x7fu<<18u))|(0x27u<<18u);add("NSA_level_zero_sampling_not_admitted",synthetic(lz),false);
 auto upper=nsa;upper[1]=(upper[1]&0xffff00ffu)|(252u<<8u);add("NSA_full_result_fits_last_four_registers",synthetic(upper),true);
 auto overflow=nsa;overflow[1]=(overflow[1]&0xffff00ffu)|(253u<<8u);
 all.push_back({"mandatory_dag_NSA_result_register_bank_overflow",synthetic(overflow),false,{},"MIMG data register range overflow"});
 add("whole_DWORD_SDWA_optional_ALU",synthetic({0x7e0c02f9u,0x00061604u,0xbf8c0070u}),true);
 auto terminalIndexed=c;terminalIndexed.insert(terminalIndexed.begin()+10,0x7e0c8904u);add("terminal_prefix_indexed_footprint_rejected",terminalIndexed,false);
 auto suffixIndexed=c;suffixIndexed.insert(suffixIndexed.begin()+12,0x7e0c8904u);add("terminal_suffix_indexed_while_raw_live_rejected",suffixIndexed,false);
 auto terminalPartial=c;terminalPartial.insert(terminalPartial.begin()+10,{0x7e0c02f9u,0x00061404u});add("terminal_prefix_partial_SDWA_write_rejected",terminalPartial,false);
 auto suffixPartial=c;suffixPartial.insert(suffixPartial.begin()+12,{0x7e0002f9u,0x00061404u});add("terminal_suffix_partial_raw_kill_rejected",suffixPartial,false);
 auto suffixExec=c;suffixExec.insert(suffixExec.begin()+12,0xbefe0380u);add("terminal_suffix_EXEC_while_raw_live_rejected",suffixExec,false);
 auto suffixM0=c;suffixM0.insert(suffixM0.begin()+12,0xbefc0380u);add("terminal_suffix_M0_while_raw_live_rejected",suffixM0,false);
 auto killedThenIndexed=c;killedThenIndexed.insert(killedThenIndexed.begin()+14,0x7e0c8904u);add("terminal_suffix_after_full_raw_kill_keeps_existing_semantics",killedThenIndexed,true);
 auto macI=c;macI.insert(macI.begin()+12,0x3e000b04u);add("terminal_suffix_VMAC_implicitly_reads_raw_I",macI,false);
 auto macJ=c;macJ.insert(macJ.begin()+12,0x3e020b04u);add("terminal_suffix_VMAC_implicitly_reads_raw_J",macJ,false);
 auto fmacI=c;fmacI.insert(fmacI.begin()+12,0x56000b04u);add("terminal_suffix_FMAC_implicitly_reads_raw_I",fmacI,false);
 auto macSafe=c;macSafe.insert(macSafe.begin()+12,0x3e0c0b04u);add("terminal_suffix_VMAC_accumulator_is_not_raw",macSafe,true);
 auto terminalBarrier=c;terminalBarrier.insert(terminalBarrier.begin()+10,0xbf8a0000u);add("terminal_prefix_barrier_before_pairs_rejected",terminalBarrier,false);
 auto wideKill=c;wideKill.insert(wideKill.begin()+12,{0xd5640000u,0x00020d04u});add("terminal_suffix_F64_raw_kill_not_admitted",wideKill,false);
 const auto mutate=[&](std::string name,Change change){add(std::move(name),c,false,std::move(change));};
 mutate("decoded_operand_disagrees_with_raw_code",[](auto& d,auto&){d.instructions[3].source0.reg=9;});
 mutate("decoded_raw_word_disagrees_with_code",[](auto& d,auto&){d.instructions[3].rawWords[0]^=1u;});
 mutate("decoded_source_modifier_disagrees_with_code",[](auto& d,auto&){d.instructions[3].source0.negate=true;});
 mutate("decoded_partial_destination",[](auto& d,auto&){d.instructions[3].destination.explicitSdwaDst=true;});
 mutate("decoded_wide_destination_covers_J",[](auto& d,auto&){d.instructions[3].destination.reg=0;d.instructions[3].is64Bit=true;});
 mutate("decoded_branch_offset_disagrees_with_raw",[](auto& d,auto&){++d.instructions[2].source0.value;});
 mutate("decoded_branch_target_disagrees_with_raw",[](auto& d,auto&){++d.instructions[2].branchTarget;});
 mutate("decoded_branch_condition_disagrees_with_raw",[](auto& d,auto&){d.instructions[2].op=RdnaOpcode::SCbranchScc1;});
 mutate("CFG_wrong_branch_target",[](auto&,auto& g){g.blocks[0].terminator.trueBlock=4;});
 mutate("CFG_wrong_branch_condition",[](auto&,auto& g){g.blocks[0].terminator.condition=BranchCondition::SccZero;});
 mutate("CFG_missing_join_predecessor",[](auto&,auto& g){g.blocks[2].predecessors={0};});
 mutate("CFG_duplicate_join_predecessor",[](auto&,auto& g){g.blocks[2].predecessors={0,0};});
 mutate("CFG_disconnected_optional_block",[](auto&,auto& g){g.blocks[1].predecessors.clear();});
 mutate("CFG_duplicate_successor",[](auto&,auto& g){g.blocks[0].successors={1,1};});
 mutate("CFG_noncontiguous_coverage",[](auto&,auto& g){++g.blocks[1].instructionBegin;});
 mutate("CFG_wrong_entry",[](auto&,auto& g){g.entryBlock=1;});
 mutate("CFG_extra_terminal_successor",[](auto&,auto& g){g.blocks[4].successors={0};});
 mutate("CFG_second_return",[](auto&,auto& g){g.blocks[1].terminator.kind=TerminatorKind::Return;});
 mutate("CFG_declared_backedge",[](auto&,auto& g){g.backEdges.push_back({3,0});});
 mutate("CFG_declared_loop",[](auto&,auto& g){g.naturalLoops.push_back({});});
 mutate("CFG_irreducible",[](auto&,auto& g){g.irreducible=true;});
 mutate("CFG_unsupported",[](auto&,auto& g){g.unsupported=true;});
 mutate("CFG_indirect_terminator_metadata",[](auto&,auto& g){g.blocks[0].terminator.indirectTargets={4};});
 add("NSA_metadata_active_count_forgery",nsaCode,false,[](auto& d,auto&){d.instructions[3].imageAddressComponents=1;});
 add("NSA_metadata_capacity_forgery",nsaCode,false,[](auto& d,auto&){d.instructions[3].imageNsaDwordCount=0;});
 add("NSA_decoded_active_register_forgery",nsaCode,false,[](auto& d,auto&){d.instructions[3].imageNsaVectorRegisters[0]=5;});
 add("NSA_decoded_padding_forgery",nsaCode,false,[](auto& d,auto&){d.instructions[3].imageNsaVectorRegisters[9]=255;});
 add("NSA_decoded_opcode_disagrees_with_raw",nsaCode,false,[](auto& d,auto&){d.instructions[3].imageOpcodeId=0x20;});
 add("NSA_decoded_flags_disagree_with_raw",nsaCode,false,[](auto& d,auto&){d.instructions[3].imageSampleFlags=0;});
 add("NSA_decoded_A16_disagrees_with_raw",nsaCode,false,[](auto& d,auto&){d.instructions[3].imageA16=true;});
 add("NSA_decoded_destination_width_forgery",nsaCode,false,[](auto& d,auto&){d.instructions[3].dataDwordCount=1;});
 return all;
}
} // namespace PublicMandatoryDagProofCases
