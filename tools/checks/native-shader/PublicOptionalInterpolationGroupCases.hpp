#pragma once
#include "RdnaDecoder/RdnaProgram.hpp"
#include "ControlFlow/ControlFlowGraph.hpp"
#include <functional>
namespace PublicOptionalInterpolationGroupCases {
using namespace ShaderRecompiler;
using Code=std::vector<std::uint32_t>;
struct Case{std::string name;Code code;bool expected;std::function<void(RdnaProgram&,ControlFlowGraph&)> change{};};
inline Code synthetic(Code optional={0xbefc031eu,0xc8100000u,0xc8110001u},Code arm={0x7e0c0304u,0xbf8c0070u},bool initialized=true,bool consume=true,Code terminal={0xbefc031eu,0xc8200000u,0xc8210001u}){
 Code c={0xbefc031eu};if(initialized)c.push_back(0x7e080280u);auto outer=c.size();c.push_back(0);
 c.insert(c.end(),optional.begin(),optional.end());auto inner=c.size();c.push_back(0);
 c.insert(c.end(),arm.begin(),arm.end());auto join=c.size();c.insert(c.end(),{0x7e0e0304u,0xbf8c0070u});auto final=c.size();
 c.insert(c.end(),terminal.begin(),terminal.end());c.insert(c.end(),{0x7e000280u,0x7e020280u,0xf800180fu,consume?0x08080404u:0x08080808u,0xbf810000u});
 c[outer]=0xbf870000u|static_cast<std::uint32_t>(final-outer-1u);c[inner]=0xbf850000u|static_cast<std::uint32_t>(join-inner-1u);return c;
}
inline std::vector<Case> cases(){std::vector<Case> all;const auto add=[&](std::string n,Code c,bool pass){all.push_back({"optional_groups_"+n,std::move(c),pass});};
 add("skipped_complete_pair_retains_initialized_output",synthetic(),true);
 add("skipped_complete_pair_output_not_consumed",synthetic({0xbefc031eu,0xc8100000u,0xc8110001u},{0xbf8c0070u,0xbf8c0070u},false,false),true); // Only paths through the complete pair reach the join.
 auto unused=synthetic({0xbefc031eu,0xc8100000u,0xc8110001u},{0xbf8c0070u,0xbf8c0070u},false,false);for(auto&w:unused)if(w==0x7e0e0304u)w=0x7e0e0280u;add("skipped_uninitialized_result_unconsumed_on_that_path",unused,true);
 add("skipped_uninitialized_result_consumed_after_join",synthetic({0xbefc031eu,0xc8100000u,0xc8110001u},{0x7e0c0304u,0xbf8c0070u},false,true),false);
 add("optional_M0_different_SGPR",synthetic({0xbefc031fu,0xc8100000u,0xc8110001u}),false);
 add("terminal_M0_different_SGPR",synthetic({0xbefc031eu,0xc8100000u,0xc8110001u},{0x7e0c0304u,0xbf8c0070u},true,true,{0xbefc031fu,0xc8200000u,0xc8210001u}),false);
 add("optional_M0_constant_changes_pair",synthetic({0xbefc0380u,0xc8100000u,0xc8110001u}),false);
 add("M0_source_redefined_on_optional_arm",synthetic({0xbefc031eu,0xc8100000u,0xc8110001u},{0xbe9e0380u,0xbf8c0070u}),false);
 add("P1_crosses_optional_branch",synthetic({0xbefc031eu,0xc8100000u}),false);
 auto splitPair=synthetic({0xbefc031eu,0xc8100000u},{0xbf8c0070u,0xbf8c0070u});
 for(auto& word:splitPair)if(word==0x7e0e0304u)word=0xc8110001u;
 add("complete_pair_split_across_optional_branch",splitPair,false);
 add("partial_P1_read_before_P2",synthetic({0xbefc031eu,0xc8100000u,0x7e0c0304u,0xc8110001u}),false);
 add("P2_without_P1_on_optional_path",synthetic({0xbefc031eu,0xc8110001u}),false);
 add("P2_different_attribute",synthetic({0xbefc031eu,0xc8100000u,0xc8110401u}),false);
 add("P2_different_channel",synthetic({0xbefc031eu,0xc8100000u,0xc8110101u}),false);
 add("optional_raw_I_read",synthetic({0xbefc031eu,0xc8100000u,0xc8110001u,0x7e0c0300u}),false);
 add("optional_raw_J_write",synthetic({0xbefc031eu,0xc8100000u,0xc8110001u,0x7e020280u}),false);
 add("optional_EXEC_write",synthetic({0xbefc031eu,0xc8100000u,0xc8110001u,0xbefe0380u}),false);
 add("optional_M0_change_while_P1_pending",synthetic({0xbefc031eu,0xc8100000u,0xbefc031eu,0xc8110001u}),false);
 add("partial_result_overwrite",synthetic({0xbefc031eu,0xc8100000u,0x7e080280u,0xc8110001u}),false);
 auto divergent=synthetic();for(auto&w:divergent)if((w&0xffff0000u)==0xbf870000u)w=(w&0xffffu)|0xbf880000u;add("EXEC_conditional_branch_not_proven",divergent,false);
 const auto mut=[&](std::string n,std::function<void(RdnaProgram&,ControlFlowGraph&)> m){all.push_back({"optional_groups_"+n,synthetic(),false,std::move(m)});};
 mut("decoded_M0_source_disagrees_with_code",[](auto& d,auto&){d.instructions[3].source0.reg=31;});
 mut("decoded_interpolation_channel_forgery",[](auto& d,auto&){d.instructions[4].source2.value=1;});
 mut("CFG_missing_optional_join_predecessor",[](auto&,auto& g){g.blocks[3].predecessors.clear();});
 mut("CFG_optional_backedge",[](auto&,auto& g){g.backEdges.push_back({3,1});});
 mut("CFG_instruction_range_outside_program",[](auto& d,auto& g){g.blocks[1].instructionEnd=static_cast<std::uint32_t>(d.instructions.size()+1u);});
 mut("CFG_reversed_instruction_range",[](auto&,auto& g){g.blocks[1].instructionBegin=g.blocks[1].instructionEnd;});
 mut("CFG_duplicate_block_identity",[](auto&,auto& g){g.blocks[1].id=g.blocks[0].id;});
 mut("CFG_UINT32_MAX_begin",[](auto&,auto& g){g.blocks[1].instructionBegin=UINT32_MAX;});
 mut("CFG_UINT32_MAX_end",[](auto&,auto& g){g.blocks[1].instructionEnd=UINT32_MAX;});
 mut("CFG_instruction_begin_after_end",[](auto&,auto& g){g.blocks[1].instructionBegin=g.blocks[1].instructionEnd+1u;});
 // Encoded SMEM loads exercise precisely the scalar-result aliases supported
 // by the existing translator. VCC is read by the unchanged VCCNZ terminator;
 // these loads do not change EXEC or the common M0 assignment.
 const auto load=[&](std::string n,std::uint32_t opcode,std::uint32_t destination,bool pass){
  const auto word=0xf4000000u|(opcode<<18u)|(destination<<6u)|26u;
  add("scalar_load_"+n,synthetic({0xbefc031eu,0xc8100000u,word,0xfa000000u,0xc8110001u}),pass);
 };
 load("VCC_LO_one_dword",8,106,true);
 load("VCC_LO_two_dwords",9,106,true);
 load("VCC_HI_one_dword",8,107,true);
 load("VCC_HI_two_dwords_overflows",9,107,false);
 load("VCC_LO_four_dwords_overflows",10,106,false);
 load("VCC_LO_eight_dwords_overflows",11,106,false);
 load("VCC_LO_sixteen_dwords_overflows",12,106,false);
 load("SGPR105_two_dwords_crosses_alias",9,105,false);
 load("wide_load_redefines_common_M0_source",9,29,false);
 load("M0_one_dword_not_VCC",8,124,false);
 load("EXEC_LO_one_dword_not_VCC",8,126,false);
 load("EXEC_LO_two_dwords_not_VCC",9,126,false);
 load("EXEC_HI_one_dword_not_VCC",8,127,false);
 load("NULL_one_dword_not_VCC",8,125,false);
 const auto loadAfterPair=[&](std::string n,std::uint32_t opcode,std::uint32_t destination,bool pass){
  const auto word=0xf4000000u|(opcode<<18u)|(destination<<6u)|26u;
  add("scalar_load_after_pair_"+n,synthetic({0xbefc031eu,0xc8100000u,0xc8110001u,word,0xfa000000u}),pass);
 };
 loadAfterPair("VCC_LO_one_dword",8,106,true);
 loadAfterPair("VCC_LO_two_dwords",9,106,true);
 loadAfterPair("VCC_HI_one_dword",8,107,true);
 loadAfterPair("VCC_HI_two_dwords_overflows",9,107,false);
 loadAfterPair("VCC_LO_four_dwords_overflows",10,106,false);
 loadAfterPair("SGPR105_two_dwords_crosses_alias",9,105,false);
 const auto loadMutation=[&](std::string n,std::function<void(RdnaProgram&,ControlFlowGraph&)> m){
  const auto word=0xf4000000u|(8u<<18u)|(107u<<6u)|26u;
  all.push_back({"optional_groups_scalar_load_"+n,synthetic({0xbefc031eu,0xc8100000u,word,0xfa000000u,0xc8110001u}),false,std::move(m)});
 };
 loadMutation("decoded_width_disagrees_with_code",[](auto& d,auto&){for(auto& i:d.instructions)if(i.family==RdnaInstructionFamily::SMEM)i.dataDwordCount=2;});
 loadMutation("decoded_VCC_alias_disagrees_with_code",[](auto& d,auto&){for(auto& i:d.instructions)if(i.family==RdnaInstructionFamily::SMEM)i.destination.kind=RdnaOperandKind::VccLo;});
 loadMutation("decoded_EXEC_alias_forgery",[](auto& d,auto&){for(auto& i:d.instructions)if(i.family==RdnaInstructionFamily::SMEM)i.destination.kind=RdnaOperandKind::ExecLo;});
 loadMutation("decoded_M0_alias_forgery",[](auto& d,auto&){for(auto& i:d.instructions)if(i.family==RdnaInstructionFamily::SMEM)i.destination.kind=RdnaOperandKind::M0;});
 return all;}
}
