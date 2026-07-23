package com.example.demo.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.demo.entity.Interview;
import com.example.demo.entity.InterviewQuestion;

public interface InterviewQuestionRepository extends JpaRepository<InterviewQuestion, Long> {

    List<InterviewQuestion> findByInterviewOrderByQuestionNumberAsc(Interview interview);
    Optional<InterviewQuestion> findById(Long id);

    Optional<InterviewQuestion> findByInterviewAndQuestionNumber(
            Interview interview,
            Integer questionNumber);

}