package com.example.demo.service;

import java.time.LocalDateTime;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import com.example.demo.entity.Application;
import com.example.demo.entity.Interview;
import com.example.demo.entity.InterviewQuestion;
import com.example.demo.repository.InterviewAnswerRepository;
import com.example.demo.repository.InterviewQuestionRepository;
import com.example.demo.repository.InterviewRepository;
import com.example.demo.entity.InterviewAnswer;
import com.example.demo.entity.Resume;
import com.example.demo.repository.ResumeRepository;
import com.example.demo.dto.AIResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class InterviewServiceImpl implements InterviewService {
	private static final String SUCCESS = "success";
	private static final String INTERVIEW_ID = "interview_id";
	private static final String QUESTION = "question";
	private static final String TOPIC_GENERAL = "General";
	private static final String DATA = "data";
	private static final Logger logger =
        LoggerFactory.getLogger(InterviewServiceImpl.class);

	@Value("${genai.service.url:http://localhost:8100}")
	private String serviceUrl;

	private final RestTemplate restTemplate = new RestTemplate();

	private final InterviewRepository interviewRepository;
	private final InterviewQuestionRepository interviewQuestionRepository;
	private final InterviewAnswerRepository interviewAnswerRepository;
	private final ResumeRepository resumeRepository;
	private final AIService aiService;

	public InterviewServiceImpl(InterviewRepository interviewRepository,
			InterviewQuestionRepository interviewQuestionRepository,
			InterviewAnswerRepository interviewAnswerRepository,
			ResumeRepository resumeRepository,
			AIService aiService) {

		this.interviewRepository = interviewRepository;
		this.interviewQuestionRepository = interviewQuestionRepository;
		this.interviewAnswerRepository = interviewAnswerRepository;
		this.resumeRepository = resumeRepository;
		this.aiService = aiService;
	}

	@Override
	public Interview startInterview(Application application) {
		Interview existingInterview = interviewRepository.findByApplication(application).orElse(null);

		if (existingInterview != null && existingInterview.getAiInterviewId() != null) {
			return existingInterview;
		}

		Interview interview = prepareInterview(existingInterview, application);

		try {
			Resume resume = resumeRepository.findByUserId(application.getCandidate().getId()).orElse(null);
			if (resume != null) {
				Interview aiInterview = tryStartGenAiSession(interview, application, resume);
				if (aiInterview != null) {
					return aiInterview;
				}
			}
		} catch (Exception e) {
			logger.error("Failed to start GenAI Interview.", e);
		}

		if (interview.getId() == null) {
			interview = interviewRepository.save(interview);
		}
		return interview;
	}

	private Interview prepareInterview(Interview existingInterview, Application application) {
		Interview interview = existingInterview != null ? existingInterview : new Interview();
		interview.setApplication(application);
		interview.setStatus("IN_PROGRESS");
		if (interview.getStartedAt() == null) {
			interview.setStartedAt(LocalDateTime.now());
		}
		if (interview.getOverallScore() == null) {
			interview.setOverallScore(0);
		}
		return interview;
	}

	private Interview tryStartGenAiSession(Interview interview, Application application, Resume resume) {
		String augmentedText = buildAugmentedResumeText(application.getJob(), resume);
		AIResponse aiResponse = aiService.analyzeResume(augmentedText);
		String candidateId = aiResponse.getSummary();

		String url = serviceUrl + "/api/v1/start_interview";
		HttpHeaders headers = new HttpHeaders();
		headers.setContentType(MediaType.APPLICATION_JSON);

		java.util.Map<String, Object> body = new java.util.HashMap<>();
		body.put("candidate_id", candidateId);
		body.put("max_questions", 10);
		body.put("starting_difficulty", "medium");

		HttpEntity<java.util.Map<String, Object>> entity = new HttpEntity<>(body, headers);
		java.util.Map<?, ?> response = restTemplate.postForObject(url, entity, java.util.Map.class);

		if (response != null && Boolean.TRUE.equals(response.get(SUCCESS))) {
			return processGenAiStartResponse(interview, response);
		}
		return null;
	}

	private String buildAugmentedResumeText(com.example.demo.entity.Job job, Resume resume) {
		StringBuilder augmentedText = new StringBuilder();
		augmentedText.append("[JOB CONTEXT]\n");
		augmentedText.append("Target Job Title (Role): ").append(job.getTitle()).append("\n");
		augmentedText.append("Target Required Skills: ").append(job.getRequiredSkills()).append("\n\n");
		augmentedText.append("[CANDIDATE RESUME TEXT]\n");
		augmentedText.append(resume.getExtractedText());
		return augmentedText.toString();
	}

	@SuppressWarnings("unchecked")
	private Interview processGenAiStartResponse(Interview interview, java.util.Map<?, ?> response) {
		java.util.Map<String, Object> data = (java.util.Map<String, Object>) response.get(DATA);
		if (data == null) {
			return null;
		}

		java.util.Map<String, Object> qMap = (java.util.Map<String, Object>) data.get(QUESTION);
		if (qMap == null) {
			return null;
		}

		String aiId = (String) data.get(INTERVIEW_ID);
		interview.setAiInterviewId(aiId);
		Interview savedInterview = interviewRepository.save(interview);

		clearExistingQuestions(savedInterview);
		saveFirstQuestion(savedInterview, qMap);
		return savedInterview;
	}

	private void clearExistingQuestions(Interview interview) {
		List<InterviewQuestion> existingQuestions = interviewQuestionRepository.findByInterviewOrderByQuestionNumberAsc(interview);
		if (!existingQuestions.isEmpty()) {
			for (InterviewQuestion eq : existingQuestions) {
				interviewAnswerRepository.findByQuestion(eq).ifPresent(interviewAnswerRepository::delete);
			}
			interviewQuestionRepository.deleteAll(existingQuestions);
		}
	}

	private void saveFirstQuestion(Interview interview, java.util.Map<String, Object> qMap) {
		InterviewQuestion firstQuestion = new InterviewQuestion();
		firstQuestion.setInterview(interview);
		firstQuestion.setQuestionNumber(1);
		firstQuestion.setQuestion((String) qMap.get(QUESTION));
		firstQuestion.setTopic((String) qMap.get("skill"));
		firstQuestion.setDifficulty(String.valueOf(qMap.get("difficulty")));
		interviewQuestionRepository.save(firstQuestion);
	}

	@Override
	public void initializeQuestions(Interview interview) {

		if (interview != null && interview.getAiInterviewId() != null) {
			return; // Do not initialize static questions if AI session is active
		}

		if (!interviewQuestionRepository.findByInterviewOrderByQuestionNumberAsc(interview).isEmpty()) {
			return;
		}

		String[] questions = { "Explain Object-Oriented Programming.", "What is Spring Boot?",
				"What is Dependency Injection?", "Explain REST API.", "What is JPA?", "What is Hibernate?",
				"Difference between HashMap and ConcurrentHashMap?", "What is JWT?", "Explain Microservices.",
				"What is Docker?" };

		for (int i = 0; i < questions.length; i++) {

			InterviewQuestion question = new InterviewQuestion();

			question.setInterview(interview);
			question.setQuestionNumber(i + 1);
			question.setQuestion(questions[i]);
			question.setTopic(TOPIC_GENERAL);
			question.setDifficulty("Medium");

			interviewQuestionRepository.save(question);
		}
	}

	@Override
	public List<InterviewQuestion> getQuestions(Interview interview) {

		return interviewQuestionRepository.findByInterviewOrderByQuestionNumberAsc(interview);
	}

	@Override
	public void saveAnswer(InterviewQuestion question, String answer) {

		if (question.getId() == null || !interviewQuestionRepository.existsById(question.getId())) {
			question.setId(null);
			question = interviewQuestionRepository.save(question);
		}

		InterviewAnswer interviewAnswer = interviewAnswerRepository.findByQuestion(question)
				.orElse(new InterviewAnswer());

		interviewAnswer.setQuestion(question);
		interviewAnswer.setCandidateAnswer(answer);
		interviewAnswer.setAnsweredAt(LocalDateTime.now());

		Interview interview = question.getInterview();
		if (interview != null) {
			if (interview.getAiInterviewId() == null) {
				interview = startInterview(interview.getApplication());
			}

			if (interview.getAiInterviewId() != null) {
				boolean success = trySubmitAnswerToAI(interview, answer, interviewAnswer);
				if (!success) {
					// Session might have expired on Python restart, re-register and retry
					logger.warn("AI Session expired or invalid. Re-registering session...");
					interview.setAiInterviewId(null);
					interview = startInterview(interview.getApplication());
					if (interview.getAiInterviewId() != null) {
						trySubmitAnswerToAI(interview, answer, interviewAnswer);
					}
				}
			} else {
				interviewAnswer.setScore(0);
				interviewAnswer.setAiFeedback("Local simulation");
			}
		}

		interviewAnswerRepository.save(interviewAnswer);
	}

	@SuppressWarnings("unchecked")
	private boolean trySubmitAnswerToAI(Interview interview, String answer, InterviewAnswer interviewAnswer) {
		try {
			java.util.Map<?, ?> response = callSubmitAnswerApi(interview.getAiInterviewId(), answer);
			if (response != null && Boolean.TRUE.equals(response.get(SUCCESS))) {
				return processSubmitAnswerResponse(interview, interviewAnswer, response);
			}
		} catch (Exception e) {
			logger.warn("Failed to evaluate answer with GenAI session {}: {}", interview.getAiInterviewId(), e.getMessage());
			interviewAnswer.setScore(0);
			interviewAnswer.setAiFeedback("FastAPI service offline or session expired. Fallback to offline evaluation.");
		}
		return false;
	}

	private java.util.Map<?, ?> callSubmitAnswerApi(String aiInterviewId, String answer) {
		String url = serviceUrl + "/api/v1/submit_answer";
		HttpHeaders headers = new HttpHeaders();
		headers.setContentType(MediaType.APPLICATION_JSON);

		java.util.Map<String, Object> body = new java.util.HashMap<>();
		body.put(INTERVIEW_ID, aiInterviewId);
		body.put("answer", answer);

		HttpEntity<java.util.Map<String, Object>> entity = new HttpEntity<>(body, headers);
		return restTemplate.postForObject(url, entity, java.util.Map.class);
	}

	@SuppressWarnings("unchecked")
	private boolean processSubmitAnswerResponse(Interview interview, InterviewAnswer interviewAnswer, java.util.Map<?, ?> response) {
		java.util.Map<String, Object> data = (java.util.Map<String, Object>) response.get(DATA);
		if (data == null) {
			return false;
		}

		java.util.Map<String, Object> eval = (java.util.Map<String, Object>) data.get("evaluation");
		if (eval == null) {
			return false;
		}

		Number scoreNum = (Number) eval.get("score");
		int score = scoreNum != null ? scoreNum.intValue() : 0;
		String feedback = (String) eval.get("feedback");

		interviewAnswer.setScore(score);
		interviewAnswer.setAiFeedback(feedback);

		updateOverallScoreIfPresent(interview, data);
		return true;
	}

	private void updateOverallScoreIfPresent(Interview interview, java.util.Map<String, Object> data) {
		Number overallScoreNum = (Number) data.get("overall_score");
		if (overallScoreNum != null) {
			interview.setOverallScore(overallScoreNum.intValue());
			interviewRepository.save(interview);
		}
	}

	@Override
	public InterviewQuestion getQuestionById(Long id) {

	    return interviewQuestionRepository.findById(id).orElseThrow();
	}

	@Override
	public InterviewQuestion getNextQuestion(Interview interview, Integer currentQuestionNumber) {
		if (interview == null || (currentQuestionNumber != null && currentQuestionNumber >= 10)) {
			return null;
		}

		if (interview.getAiInterviewId() == null) {
			interview = startInterview(interview.getApplication());
		}

		InterviewQuestion existingNext = findExistingNextQuestion(interview, currentQuestionNumber);
		if (existingNext != null) {
			return existingNext;
		}

		if (interview.getAiInterviewId() != null) {
			return fetchNextQuestionFromAi(interview, currentQuestionNumber);
		}

		return null;
	}

	private InterviewQuestion findExistingNextQuestion(Interview interview, Integer currentQuestionNumber) {
		InterviewQuestion nextQuestion = interviewQuestionRepository
				.findByInterviewAndQuestionNumber(interview, currentQuestionNumber + 1)
				.orElse(null);

		if (nextQuestion != null && !TOPIC_GENERAL.equals(nextQuestion.getTopic())) {
			return nextQuestion;
		}
		return null;
	}

	@SuppressWarnings("unchecked")
	private InterviewQuestion fetchNextQuestionFromAi(Interview interview, Integer currentQuestionNumber) {
		try {
			String url = serviceUrl + "/api/v1/next_question";
			HttpHeaders headers = new HttpHeaders();
			headers.setContentType(MediaType.APPLICATION_JSON);

			java.util.Map<String, Object> body = new java.util.HashMap<>();
			body.put(INTERVIEW_ID, interview.getAiInterviewId());

			HttpEntity<java.util.Map<String, Object>> entity = new HttpEntity<>(body, headers);
			java.util.Map<?, ?> response = restTemplate.postForObject(url, entity, java.util.Map.class);

			if (response != null && Boolean.TRUE.equals(response.get(SUCCESS))) {
				return parseNextQuestionResponse(interview, currentQuestionNumber, response);
			}
		} catch (Exception e) {
			logger.error("Failed to fetch next question from GenAI: ", e);
		}
		return null;
	}

	@SuppressWarnings("unchecked")
	private InterviewQuestion parseNextQuestionResponse(Interview interview, Integer currentQuestionNumber, java.util.Map<?, ?> response) {
		java.util.Map<String, Object> data = (java.util.Map<String, Object>) response.get(DATA);
		if (data == null) {
			return null;
		}

		String status = (String) data.get("interview_status");
		if ("completed".equalsIgnoreCase(status)) {
			return null;
		}

		java.util.Map<String, Object> qMap = (java.util.Map<String, Object>) data.get(QUESTION);
		if (qMap != null) {
			InterviewQuestion nextQuestion = new InterviewQuestion();
			nextQuestion.setInterview(interview);
			nextQuestion.setQuestionNumber(currentQuestionNumber + 1);
			nextQuestion.setQuestion((String) qMap.get(QUESTION));
			nextQuestion.setTopic((String) qMap.get("skill"));
			nextQuestion.setDifficulty(String.valueOf(qMap.get("difficulty")));

			return interviewQuestionRepository.save(nextQuestion);
		}
		return null;
	}

	@Override
	public void endInterview(Interview interview) {
		if (interview == null || interview.getAiInterviewId() == null) {
			return;
		}

		try {
			java.util.Map<?, ?> response = callEndInterviewApi(interview.getAiInterviewId());
			if (response != null && Boolean.TRUE.equals(response.get(SUCCESS))) {
				processEndInterviewResponse(interview, response);
			}
		} catch (Exception e) {
			logger.error("Failed to end GenAI Interview: ", e);
		}
	}

	private java.util.Map<?, ?> callEndInterviewApi(String aiInterviewId) {
		String url = serviceUrl + "/api/v1/end_interview";
		HttpHeaders headers = new HttpHeaders();
		headers.setContentType(MediaType.APPLICATION_JSON);

		java.util.Map<String, Object> body = new java.util.HashMap<>();
		body.put(INTERVIEW_ID, aiInterviewId);

		HttpEntity<java.util.Map<String, Object>> entity = new HttpEntity<>(body, headers);
		return restTemplate.postForObject(url, entity, java.util.Map.class);
	}

	@SuppressWarnings("unchecked")
	private void processEndInterviewResponse(Interview interview, java.util.Map<?, ?> response) {
		java.util.Map<String, Object> data = (java.util.Map<String, Object>) response.get(DATA);
		if (data == null) {
			return;
		}

		java.util.Map<String, Object> report = (java.util.Map<String, Object>) data.get("report");
		if (report != null) {
			Number overallScoreNum = (Number) report.get("overall_score");
			if (overallScoreNum != null) {
				interview.setOverallScore(overallScoreNum.intValue());
			}
		}
	}
}