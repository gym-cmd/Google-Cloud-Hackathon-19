from google.adk.agents import Agent

from learning_agent.agent import (
    MODEL,
    assessment_agent,
    curriculum_agent,
    quiz_agent,
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

    def test_has_all_sub_agents(self):
        sub_names = [a.name for a in root_agent.sub_agents]
        assert "assessment_agent" in sub_names
        assert "curriculum_agent" in sub_names
        assert "quiz_agent" in sub_names

    def test_sub_agent_count(self):
        assert len(root_agent.sub_agents) == 3

    def test_instruction_references_sub_agents(self):
        assert "@assessment_agent" in root_agent.instruction
        assert "@curriculum_agent" in root_agent.instruction
        assert "@quiz_agent" in root_agent.instruction

    def test_instruction_describes_workflow(self):
        assert "Greet" in root_agent.instruction
        assert "Assessment" in root_agent.instruction
        assert "Curriculum" in root_agent.instruction
        assert "Quiz" in root_agent.instruction
