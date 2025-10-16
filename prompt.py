# Call load_requirement directly (no need for core.load_and_validate_requirement)
req_obj = load_requirement(requirement_source)

prompt = f"""Requirement loaded: {req_obj.id}
  {req_obj.model_dump_json(indent=2)}

  Please process this requirement..."""

# Load and validate requirement (DETERMINISTIC PREPROCESSING)
req_obj = load_requirement(requirement_source)

  # Refactored prompt with pre-loaded requirement
prompt = f"""The requirement has been successfully loaded and validated.

**Requirement Details:**
- ID: {req_obj.id}
- Title: {req_obj.title}
- User Story ID: {req_obj.user_story_id}

**Full Requirement:**
{req_obj.model_dump_json(indent=2)}

**Your Task:**
Using the requirement details provided above, please:
1. Generate the necessary code as specified in the requirement
2. Create a GitHub Pull Request (PR) for the changes
3. Send email notifications as specified in the requirement

The requirement file corresponds to user story ID: {req.user_story_id}. Please proceed with implementation, PR creation, and notifications."""