package com.example.demo.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import com.example.demo.dto.AIResponse;
import java.util.List;
import java.util.Map;
import com.example.demo.exception.AIServiceException;

@Service
public class AIServiceImpl implements AIService {

    @Value("${genai.service.url:http://localhost:8100}")
    private String serviceUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    @Override
    public AIResponse analyzeResume(String text) {

        String url = serviceUrl + "/api/v1/upload_resume";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("resume_text", text);

        HttpEntity<MultiValueMap<String, Object>> entity =
                new HttpEntity<>(body, headers);

        try {
            Map<?, ?> response = restTemplate.postForObject(url, entity, Map.class);
            AIResponse aiResponse = new AIResponse();

            if (response != null && Boolean.TRUE.equals(response.get("success"))) {
                Map<String, Object> data = (Map<String, Object>) response.get("data");
                if (data != null) {
                    List<String> skills = (List<String>) data.get("skills");
                    List<String> domains = (List<String>) data.get("primary_domains");
                    Double experience = null;
                    if (data.get("years_of_experience") instanceof Number number) {
                        experience = number.doubleValue();
                    }

                    aiResponse.setSkills(skills);
                    aiResponse.setJobRoles(domains);
                    aiResponse.setExperienceLevel(experience != null && experience > 0 ? experience + " Years" : "Fresher");
                    aiResponse.setScore(50 + Math.min(skills != null ? skills.size() * 5 : 0, 40));
                    aiResponse.setSummary((String) data.get("candidate_id")); // Store candidate_id in summary
                    aiResponse.setStrengths(List.of("Parsed by FastAPI GenAI System."));
                    aiResponse.setWeaknesses(List.of("Click Start AI Interview to begin dynamic screening."));
                    return aiResponse;
                }
            }
        } catch (Exception e) {
            // Re-throw to allow local fallback in ResumeServiceImpl.java
            throw new AIServiceException("FastAPI microservice call failed: " + e.getMessage(), e);
        }
        throw new AIServiceException("Invalid response format from FastAPI microservice.");
    }
}