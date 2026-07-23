package com.example.demo.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.demo.entity.CandidateSkill;
import com.example.demo.entity.User;

import javax.transaction.Transactional;

public interface CandidateSkillRepository extends JpaRepository<CandidateSkill, Long> {

    List<CandidateSkill> findByUser(User user);

    @Transactional
    void deleteByUser(User user);

}