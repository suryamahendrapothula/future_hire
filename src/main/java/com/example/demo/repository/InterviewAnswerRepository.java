package com.example.demo.repository;


import org.springframework.data.jpa.repository.JpaRepository;

import com.example.demo.entity.InterviewAnswer;
import com.example.demo.entity.InterviewQuestion;
import java.util.Optional;

public interface InterviewAnswerRepository extends JpaRepository<InterviewAnswer, Long> {


    Optional<InterviewAnswer> findByQuestion(InterviewQuestion question);

}