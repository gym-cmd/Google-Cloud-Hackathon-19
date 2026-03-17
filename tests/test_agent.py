from google.adk.agents import Agent
from google.adk.tools import AgentTool

from learning_agent.agent import (
    MODEL,
    assessment_agent,
    assessment_tool,
    curriculum_agent,
    curriculum_tool,
    quiz_agent,
    quiz_tool,
    root_agent,
)


class TestModelConstant:
    def test_model_is_gemini_flash(self):
        assert MODEL == "gemini-2.5-flash"


class TestAssessmentAgent:
    def test_type(self):
        assert isinstance(assessment_agent, Agent)

    def test_name(self):
        assert assessment_agent.name == "assessment_agent"

    def test_model(self):
        assert assessment_agent.model == MODEL

    def test_no_tools(self):
        assert not assessment_agent.tools

    def test_instruction_mentions_json_format(self):
        assert "assessment_complete" in assessment_agent.instruction
        assert "user_context" in assessment_agent.instruction

    def test_instruction_limits_turns(self):
        assert "3" in assessment_agent.instruction
        assert "5" in assessment_agent.instruction


class TestCurriculumAgent:
    def test_type(self):
        assert isinstance(curriculum_agent, Agent)

    def test_name(self):
        assert curriculum_agent.name == "curriculum_agent"

    def test_model(self):
        assert curriculum_agent.model == MODEL

    def test_no_tools(self):
        assert not curriculum_agent.tools

    def test_instruction_requires_json(self):
        assert '"steps"' in curriculum_agent.instruction

    def test_instruction_specifies_step_count(self):
        assert "4" in curriculum_agent.instruction
        assert "6" in curriculum_agent.instruction


class TestQuizAgent:
    def test_type(self):
        assert isinstance(quiz_agent, Agent)

    def test_name(self):
        assert quiz_agent.name == "quiz_agent"

    def test_model(self):
        assert quiz_agent.model == MODEL

    def test_no_tools(self):
        assert not quiz_agent.tools

    def test_instruction_has_generate_mode(self):
        assert "correct_index" in quiz_agent.instruction

    def test_instruction_has_evaluate_mode(self):
        assert "2/3" in quiz_agent.instruction

    def test_instruction_specifies_3_questions(self):
        assert "3 multiple-choice" in quiz_agent.instruction


class TestRootAgent:
    def test_type(self):
        assert isinstance(root_agent, Agent)

    def test_name(self):
        assert root_agent.name == "learning_tutor"

    def test_model(self):
        assert root_agent.model == MODEL

    def test_has_all_tools(self):
        tool_names = [tool.name for tool in root_agent.tools]
        assert "assessment_agent" in tool_names
        assert "curriculum_agent" in tool_names
        assert "quiz_agent" in tool_names

    def test_tool_count(self):
        assert len(root_agent.tools) == 3

    def test_instruction_references_tools(self):
        assert "`assessment_agent` tool" in root_agent.instruction
        assert "`curriculum_agent` tool" in root_agent.instruction
        assert "`quiz_agent` tool" in root_agent.instruction

    def test_no_sub_agents_configured(self):
        assert not root_agent.sub_agents

    def test_instruction_describes_workflow(self):
        assert "Greet" in root_agent.instruction
        assert "Assessment" in root_agent.instruction
        assert "Curriculum" in root_agent.instruction
        assert "Quiz" in root_agent.instruction


class TestAgentTools:
    def test_assessment_tool_type(self):
        assert isinstance(assessment_tool, AgentTool)

    def test_curriculum_tool_type(self):
        assert isinstance(curriculum_tool, AgentTool)

    def test_quiz_tool_type(self):
        assert isinstance(quiz_tool, AgentTool)

    def test_tools_preserve_agent_names(self):
        assert assessment_tool.name == "assessment_agent"
        assert curriculum_tool.name == "curriculum_agent"
        assert quiz_tool.name == "quiz_agent"
