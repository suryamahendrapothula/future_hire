package com.example.demo.service;

import com.example.demo.entity.Application;
import com.example.demo.entity.Interview;
import java.util.List;
import com.example.demo.entity.InterviewQuestion;

public interface InterviewService {

    Interview startInterview(Application application);
    void initializeQuestions(Interview interview);
    List<InterviewQuestion> getQuestions(Interview interview);
    void saveAnswer(InterviewQuestion question, String answer);
    InterviewQuestion getQuestionById(Long id);

    InterviewQuestion getNextQuestion(Interview interview, Integer currentQuestionNumber);
    void endInterview(Interview interview);
}