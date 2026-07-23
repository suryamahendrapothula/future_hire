package com.example.demo.entity;

import javax.persistence.*;

@Entity
@Table(name = "resumes")
public class Resume {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String fileName;

    private String filePath;

    @OneToOne
    @JoinColumn(name="user_id")
    private User user;
    @Column(columnDefinition = "LONGTEXT")
    private String extractedText;
    private Integer aiScore;
    @Column(columnDefinition = "LONGTEXT")
    private String summary;

    @Column(columnDefinition = "LONGTEXT")
    private String strengths;

    @Column(columnDefinition = "LONGTEXT")
    private String weaknesses;

    @Column(columnDefinition = "LONGTEXT")
    private String jobRoles;

    private String experienceLevel;
	public String getSummary() {
		return summary;
	}
	public void setSummary(String summary) {
		this.summary = summary;
	}
	public String getStrengths() {
		return strengths;
	}
	public void setStrengths(String strengths) {
		this.strengths = strengths;
	}
	public String getWeaknesses() {
		return weaknesses;
	}
	public void setWeaknesses(String weaknesses) {
		this.weaknesses = weaknesses;
	}
	public String getJobRoles() {
		return jobRoles;
	}
	public void setJobRoles(String jobRoles) {
		this.jobRoles = jobRoles;
	}
	public String getExperienceLevel() {
		return experienceLevel;
	}
	public void setExperienceLevel(String experienceLevel) {
		this.experienceLevel = experienceLevel;
	}
	public Long getId() {
		return id;
	}
	public void setId(Long id) {
		this.id = id;
	}
	public String getFileName() {
		return fileName;
	}
	public void setFileName(String fileName) {
		this.fileName = fileName;
	}
	public String getFilePath() {
		return filePath;
	}
	public void setFilePath(String filePath) {
		this.filePath = filePath;
	}
	public User getUser() {
		return user;
	}
	public void setUser(User user) {
		this.user = user;
	}
	public String getExtractedText() {
		return extractedText;
	}
	public void setExtractedText(String extractedText) {
		this.extractedText = extractedText;
	}
	public Integer getAiScore() {
		return aiScore;
	}
	public void setAiScore(Integer aiScore) {
		this.aiScore = aiScore;
	}
	public Resume() {
	}
	public Resume(Long id, String fileName, String filePath, User user, String extractedText, Integer aiScore) {
		super();
		this.id = id;
		this.fileName = fileName;
		this.filePath = filePath;
		this.user = user;
		this.extractedText = extractedText;
		this.aiScore = aiScore;
	}
    
    
}