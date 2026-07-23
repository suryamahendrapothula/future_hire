package com.example.demo.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.demo.entity.Resume;
import com.example.demo.entity.User;

public interface ResumeRepository extends JpaRepository<Resume,Long>{

	Optional<Resume> findByUserId(Long id);
	boolean existsByUser(User user);
	
}