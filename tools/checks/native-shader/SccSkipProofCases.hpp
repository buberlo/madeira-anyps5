#pragma once
#include "RdnaDecoder/RdnaProgram.hpp"
#include "ControlFlow/ControlFlowGraph.hpp"
#include <functional>
#include <string>
#include <vector>
// Entirely synthetic encodings; no serialized request or game bytes.
namespace PublicSccSkipProofCases {
using namespace ShaderRecompiler;
using Code=std::vector<std::uint32_t>;
using Change=std::function<void(RdnaProgram&,ControlFlowGraph&)>;
struct Case {std::string name;Code code;bool expected;Change change{};};
inline Code synthetic(){return {0xc8100000u,0xc8110001u,0xbf840002u,0x200c0880u,0xbf8c0070u,0xc8140000u,0xc8150001u,0x7e000280u,0x7e020280u,0xf800180fu,0x05050404u,0xbf810000u};}
inline std::vector<Case> cases(){
 std::vector<Case> all;
 const auto add=[&](std::string name,Code code,bool expected,Change change={}){
  all.push_back({"scc_skip_"+name,std::move(code),expected,std::move(change)});
 };
 auto c=synthetic();add("uniform_scc0_skip_with_unchanged_IJ",c,true);
 auto inverse=c;inverse[2]=0xbf850002u;add("uniform_scc1_skip_with_unchanged_IJ",inverse,true);
 auto mutate=[&](const std::string& n,Change change){add(n,c,false,change);};
 auto readI=c;readI[3]=0x7e0c0300u;add("optional_arm_raw_I_read",readI,false);
 auto readJ=c;readJ[3]=0x7e0c0301u;add("optional_arm_raw_J_read",readJ,false);
 auto writeI=c;writeI[3]=0x7e000304u;add("optional_arm_raw_I_write",writeI,false);
 auto writeJ=c;writeJ[3]=0x7e020304u;add("optional_arm_raw_J_write",writeJ,false);
 auto exec=c;exec[3]=0xbefe0380u;add("optional_arm_EXEC_change",exec,false);
 auto barrier=c;barrier[3]=0xbf8a0000u;add("optional_arm_barrier",barrier,false);
 auto unknown=c;unknown[3]=0xbf800000u;add("optional_arm_unknown_effect",unknown,false);
 mutate("partial_P1_crosses_branch",[](auto&d,auto&){d.instructions[1].op=RdnaOpcode::SNop;});
 mutate("optional_interpolation_not_admitted",[](auto&d,auto&){d.instructions[3]=d.instructions[0];});
 mutate("join_mismatched_P2_attribute",[](auto&d,auto&){d.instructions[6].source1.value=1;});
 mutate("join_modified_I",[](auto&d,auto&){d.instructions[5].source0.negate=true;});
 mutate("join_modified_J",[](auto&d,auto&){d.instructions[6].source0.absolute=true;});
 mutate("join_copied_I_pair",[](auto&d,auto&){d.instructions[5].source0.reg=4;d.instructions[6].source0.reg=5;});
 mutate("max_partial_destination",[](auto&d,auto&){d.instructions[3].destination.explicitSdwaDst=true;});
 mutate("max_cross_lane_source",[](auto&d,auto&){d.instructions[3].source1.dpp=true;});
 mutate("max_wide_write_covers_J",[](auto&d,auto&){d.instructions[3].destination.reg=0;d.instructions[3].dataDwordCount=2;});
 mutate("max_wrong_raw_encoding",[](auto&d,auto&){d.instructions[3].rawWords[0]^=1u;});
 mutate("max_modified_zero_source",[](auto&d,auto&){d.instructions[3].source0.negate=true;});
 mutate("max_extra_source",[](auto&d,auto&){d.instructions[3].source2.kind=RdnaOperandKind::VectorRegister;d.instructions[3].source2.reg=0;});
 mutate("max_second_destination",[](auto&d,auto&){d.instructions[3].destination2.kind=RdnaOperandKind::VectorRegister;d.instructions[3].destination2.reg=0;});
 mutate("wait_vector_payload",[](auto&d,auto&){d.instructions[4].source0.kind=RdnaOperandKind::VectorRegister;d.instructions[4].source0.reg=0;});
 mutate("wait_wrong_raw_encoding",[](auto&d,auto&){d.instructions[4].rawWords[0]^=1u;});
 mutate("wait_EXEC_destination",[](auto&d,auto&){d.instructions[4].destination.kind=RdnaOperandKind::ExecLo;});
 mutate("wrong_branch_target",[](auto&,auto&g){g.blocks[0].terminator.trueBlock=1;});
 mutate("wrong_branch_successor",[](auto&,auto&g){g.blocks[0].successors={1};});
 mutate("missing_join_predecessor",[](auto&,auto&g){g.blocks[2].predecessors={0};});
 mutate("duplicate_join_predecessor",[](auto&,auto&g){g.blocks[2].predecessors={0,0};});
 mutate("extra_optional_predecessor",[](auto&,auto&g){g.blocks[1].predecessors={0,2};});
 mutate("optional_nested_conditional",[](auto&,auto&g){g.blocks[1].terminator.kind=TerminatorKind::ConditionalBranch;});
 mutate("unknown_branch_condition",[](auto&,auto&g){g.blocks[0].terminator.condition=BranchCondition::Unknown;});
 auto vectorBranch=c;vectorBranch[2]=0xbf860002u;add("VCC_condition_not_uniform_SCC_proof",vectorBranch,false);
 auto execBranch=c;execBranch[2]=0xbf880002u;add("EXEC_condition_not_uniform_SCC_proof",execBranch,false);
 mutate("CFG_unsupported",[](auto&,auto&g){g.unsupported=true;});
 mutate("CFG_irreducible",[](auto&,auto&g){g.irreducible=true;});
 mutate("CFG_back_edge",[](auto&,auto&g){g.backEdges.push_back({1,0});});
 mutate("CFG_noncontiguous_coverage",[](auto&,auto&g){++g.blocks[1].instructionBegin;});
 mutate("CFG_extra_join_successor",[](auto&,auto&g){g.blocks[2].successors={0};});
 mutate("branch_raw_target_disagreement",[](auto&d,auto&){d.instructions[2].source0.value=1;});
 mutate("branch_instruction_condition_disagreement",[](auto&d,auto&){d.instructions[2].op=RdnaOpcode::SCbranchScc1;});
 auto completeAfter=c;completeAfter[1]=0xbf8c0070u;completeAfter[3]=0x200c1080u;completeAfter[5]=0xc8110001u;completeAfter[6]=0x7e100280u;add("partial_P1_completed_only_after_join",completeAfter,false);
 mutate("branch_raw_word_disagreement",[](auto&d,auto&){d.instructions[2].rawWords[0]^=1u;});
 mutate("branch_source_count_disagreement",[](auto&d,auto&){d.instructions[2].sourceCount=1;});
 mutate("branch_signed_backwards_offset",[](auto&d,auto&){d.instructions[2].source0.value=0xffffu;d.instructions[2].rawWords[0]=0xbf84ffffu;});
 mutate("optional_arm_new_memory_effect",[](auto&d,auto&){d.instructions[3].family=RdnaInstructionFamily::MIMG;d.instructions[3].op=RdnaOpcode::ImageLoad;});
 return all;
}
} // namespace PublicSccSkipProofCases
