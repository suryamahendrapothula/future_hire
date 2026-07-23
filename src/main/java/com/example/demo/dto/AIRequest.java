package com.example.demo.dto;

public class AIRequest {

    private String text;

    public AIRequest() {
    }

    public AIRequest(String text) {
        this.text = text;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }
}