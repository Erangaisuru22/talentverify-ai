# TalentVerify Interview Marking Guide

## Scoring model

Before the interview stage, recruiters can inspect the candidate's Multi-Source Technical Skills
Matrix. It may contain CV, experience, project, GitHub, portfolio, and LinkedIn source indicators.
Those sources help select interview questions, but a link being available is not proof of skill.

The interview is scored out of 6: Language Fluency /1 and Soft Skills /5. This assists the recruiter and never makes the final hiring decision.

When a recruiter assigns an interview weight inside a job's 100-mark configuration, convert the raw result proportionally:

    interview_contribution = round((raw_interview_score / 6) * interview_weight, 1)

Example: 4.5/6 with an interview weight of 12 contributes 9/12. Never add the raw /6 result directly to the /100 total.

## Language Fluency — 1 mark

Assess Tamil, Sinhala, and English through short job-related conversations, only when required by the role.

- 1.00: Fluent and confident in all three languages.
- 0.75: Fluent in two and conversational in the third.
- 0.50: Fluent in two only.
- 0.25: Fluent in one only.
- 0.00: Unable to communicate effectively in the required languages.

Record each language as Fluent, Conversational, Basic, Not demonstrated, or Not assessed. Not assessed is not failure.

## Soft Skills — 5 marks

Ask for real examples or practical scenario responses covering Communication, Problem Solving, Ownership, Teamwork, Adaptability, Feedback Handling, and Critical Thinking.

Rate every dimension from 0 to 5:

- 5: Specific example, clear personal actions and outcome, strong reasoning and reflection.
- 4: Strong evidence with a minor detail, outcome, or reflection gap.
- 3: Relevant example but limited depth or measurable outcome.
- 2: Weak example with unclear personal contribution or reasoning.
- 1: Vague claim with almost no behavioural evidence.
- 0: No relevant answer or assessable evidence.

Calculate:

    soft_skills_score = round(sum(seven_dimension_ratings) / 7, 1)
    raw_interview_score = language_score + soft_skills_score

For each dimension store the rating, question, candidate example, evidence note, interviewer ID, and timestamp. Do not score accent, confidence, personality similarity, name, location, nationality, photograph, or protected characteristics.

## Behavioural questions

1. Communication: Explain a time you presented a technical problem to a non-technical person.
2. Problem Solving: Describe a difficult problem, root-cause analysis, solution, and verification.
3. Ownership: Describe a project problem you were responsible for and what you did.
4. Teamwork: Describe a technical disagreement and how the decision was reached.
5. Adaptability: Describe learning a technology or changing direction quickly.
6. Feedback Handling: Describe critical feedback and the change you made afterward.
7. Critical Thinking: Evaluate a solution that works but is costly, hard to maintain, and may not scale.

## Recruiter-configured weights

All job-category weights must be between 0 and 100 and sum to exactly 100. Save them before evaluation. A change creates a new scoring version and must not silently recalculate historical results.

Normalize each category with:

    category_contribution = round((raw_marks / raw_maximum) * configured_weight, 1)
    final_score = sum(all_category_contributions)

The backend validates and calculates the total. Never trust an AI-generated total.

## Result template

    Candidate Name:
    Tamil: Fluent / Conversational / Basic / Not demonstrated / Not assessed
    Sinhala: Fluent / Conversational / Basic / Not demonstrated / Not assessed
    English: Fluent / Conversational / Basic / Not demonstrated / Not assessed
    Language Fluency: __ / 1
    Communication: Strong / Average / Weak
    Problem Solving: Strong / Average / Weak
    Ownership: Strong / Average / Weak
    Teamwork: Strong / Average / Weak
    Adaptability: Strong / Average / Weak
    Feedback Handling: Strong / Average / Weak
    Critical Thinking: Strong / Average / Weak
    Soft Skills Score: __ / 5
    Raw Interview Score: __ / 6
    Weighted Interview Contribution: __ / configured interview weight
    Strengths:
    Concerns:
    Evidence Notes:
    Recruiter Decision: Strong Hire / Hire / Consider / No Hire

The recruiter decision is manual. Gemini may summarize a transcript and propose editable evidence, but it must not invent examples, infer unassessed language ability, submit ratings without interviewer confirmation, or choose the final recommendation.
