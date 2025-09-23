#!/usr/bin/env python3
"""
BMAD Web Interface

Simple web interface for BMAD artifact creation using built-in HTTP server.
"""

import json
import os
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

class BMADWebHandler(BaseHTTPRequestHandler):
    """HTTP request handler for BMAD web interface."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self._serve_html_page('index')
        elif path == '/bmad/forms/prd':
            self._serve_html_page('prd_form')
        elif path == '/bmad/forms/architecture':
            self._serve_html_page('arch_form')
        elif path == '/bmad/forms/story':
            self._serve_html_page('story_form')
        elif path == '/bmad/api/health':
            self._send_json_response(200, {
                "status": "healthy",
                "service": "bmad-web-interface",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/bmad/api/prd/create':
            self._handle_prd_creation()
        elif path == '/bmad/api/architecture/create':
            self._handle_architecture_creation()
        elif path == '/bmad/api/story/create':
            self._handle_story_creation()
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def _serve_html_page(self, page_type: str):
        """Serve HTML page."""
        html_content = self._get_html_content(page_type)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def _get_html_content(self, page_type: str) -> str:
        """Get HTML content for different page types."""
        if page_type == 'index':
            return self._get_index_html()
        elif page_type == 'prd_form':
            return self._get_prd_form_html()
        elif page_type == 'arch_form':
            return self._get_architecture_form_html()
        elif page_type == 'story_form':
            return self._get_story_form_html()
        else:
            return "<html><body><h1>Page not found</h1></body></html>"
    
    def _get_index_html(self) -> str:
        """Get index page HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BMAD Artifact Creator</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .form-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 2px solid #e9ecef;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .form-card:hover {
            border-color: #007bff;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,123,255,0.2);
        }
        .form-card h3 {
            color: #007bff;
            margin-bottom: 10px;
        }
        .form-card p {
            color: #666;
            margin-bottom: 15px;
        }
        .btn {
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: background 0.3s ease;
        }
        .btn:hover {
            background: #0056b3;
        }
        .status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 BMAD Artifact Creator</h1>
        <p style="text-align: center; color: #666; margin-bottom: 30px;">
            Create professional PRDs, Architecture documents, and User Stories with AI assistance
        </p>
        
        <div class="form-grid">
            <div class="form-card" onclick="location.href='/bmad/forms/prd'">
                <h3>📋 Product Requirements Document</h3>
                <p>Define product features, requirements, and specifications</p>
                <a href="/bmad/forms/prd" class="btn">Create PRD</a>
            </div>
            
            <div class="form-card" onclick="location.href='/bmad/forms/architecture'">
                <h3>🏗️ System Architecture</h3>
                <p>Design system components, technology stack, and architecture patterns</p>
                <a href="/bmad/forms/architecture" class="btn">Create Architecture</a>
            </div>
            
            <div class="form-card" onclick="location.href='/bmad/forms/story'">
                <h3>📖 User Stories</h3>
                <p>Define user stories, acceptance criteria, and implementation plans</p>
                <a href="/bmad/forms/story" class="btn">Create Stories</a>
            </div>
        </div>
        
        <div id="status" class="status" style="display: none;"></div>
    </div>
    
    <script>
        // Check API health on load
        fetch('/bmad/api/health')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'healthy') {
                    showStatus('✅ BMAD API is healthy and ready', 'success');
                } else {
                    showStatus('⚠️ BMAD API is not responding properly', 'error');
                }
            })
            .catch(error => {
                showStatus('❌ Cannot connect to BMAD API', 'error');
            });
        
        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';
        }
    </script>
</body>
</html>
        """
    
    def _get_prd_form_html(self) -> str:
        """Get PRD form HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create PRD - BMAD</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        input, textarea, select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #007bff;
        }
        textarea {
            height: 100px;
            resize: vertical;
        }
        .btn {
            background: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            transition: background 0.3s ease;
        }
        .btn:hover {
            background: #0056b3;
        }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover {
            background: #545b62;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 5px;
            display: none;
        }
        .result.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .result.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Create Product Requirements Document</h1>
        
        <form id="prdForm">
            <div class="form-group">
                <label for="projectName">Project Name *</label>
                <input type="text" id="projectName" name="projectName" required>
            </div>
            
            <div class="form-group">
                <label for="projectDescription">Project Description *</label>
                <textarea id="projectDescription" name="projectDescription" required 
                    placeholder="Describe what this project aims to achieve..."></textarea>
            </div>
            
            <div class="form-group">
                <label for="targetUsers">Target Users</label>
                <input type="text" id="targetUsers" name="targetUsers" 
                    placeholder="e.g., Developers, End Users, Administrators">
            </div>
            
            <div class="form-group">
                <label for="businessGoals">Business Goals</label>
                <textarea id="businessGoals" name="businessGoals" 
                    placeholder="What business objectives will this project achieve?"></textarea>
            </div>
            
            <div class="form-group">
                <label for="technicalConstraints">Technical Constraints</label>
                <textarea id="technicalConstraints" name="technicalConstraints" 
                    placeholder="Any technical limitations or requirements..."></textarea>
            </div>
            
            <div class="form-group">
                <label for="timeline">Timeline</label>
                <input type="text" id="timeline" name="timeline" 
                    placeholder="e.g., 3 months, Q2 2024">
            </div>
            
            <div class="form-group">
                <label for="priority">Priority</label>
                <select id="priority" name="priority">
                    <option value="low">Low</option>
                    <option value="medium" selected>Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                </select>
            </div>
            
            <button type="submit" class="btn">🚀 Generate PRD</button>
            <a href="/" class="btn btn-secondary">← Back to Home</a>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Generating your PRD with AI...</p>
        </div>
        
        <div id="result" class="result"></div>
    </div>
    
    <script>
        document.getElementById('prdForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch('/bmad/api/prd/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showResult('✅ PRD created successfully!<br><br>' + 
                        '<strong>Document ID:</strong> ' + result.document_id + '<br>' +
                        '<strong>Status:</strong> ' + result.status + '<br><br>' +
                        '<strong>Content Preview:</strong><br>' +
                        '<pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">' +
                        result.content.substring(0, 500) + '...</pre>', 'success');
                } else {
                    showResult('❌ Error: ' + result.error, 'error');
                }
            } catch (error) {
                showResult('❌ Network error: ' + error.message, 'error');
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        });
        
        function showResult(message, type) {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = message;
            resultDiv.className = 'result ' + type;
            resultDiv.style.display = 'block';
        }
    </script>
</body>
</html>
        """
    
    def _get_architecture_form_html(self) -> str:
        """Get Architecture form HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Architecture - BMAD</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        input, textarea, select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #007bff;
        }
        textarea {
            height: 100px;
            resize: vertical;
        }
        .btn {
            background: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            transition: background 0.3s ease;
        }
        .btn:hover {
            background: #0056b3;
        }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover {
            background: #545b62;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 5px;
            display: none;
        }
        .result.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .result.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ Create System Architecture</h1>
        
        <form id="archForm">
            <div class="form-group">
                <label for="projectName">Project Name *</label>
                <input type="text" id="projectName" name="projectName" required>
            </div>
            
            <div class="form-group">
                <label for="prdReference">PRD Reference</label>
                <input type="text" id="prdReference" name="prdReference" 
                    placeholder="Reference to existing PRD or requirements">
            </div>
            
            <div class="form-group">
                <label for="technicalConstraints">Technical Constraints *</label>
                <textarea id="technicalConstraints" name="technicalConstraints" required
                    placeholder="Describe technical limitations, performance requirements, etc..."></textarea>
            </div>
            
            <div class="form-group">
                <label for="performanceRequirements">Performance Requirements</label>
                <textarea id="performanceRequirements" name="performanceRequirements" 
                    placeholder="Response time, throughput, scalability requirements..."></textarea>
            </div>
            
            <div class="form-group">
                <label for="integrationPoints">Integration Points</label>
                <textarea id="integrationPoints" name="integrationPoints" 
                    placeholder="External systems, APIs, databases to integrate with..."></textarea>
            </div>
            
            <div class="form-group">
                <label for="architectureStyle">Architecture Style</label>
                <select id="architectureStyle" name="architectureStyle">
                    <option value="microservices">Microservices</option>
                    <option value="monolithic">Monolithic</option>
                    <option value="serverless">Serverless</option>
                    <option value="event-driven">Event-Driven</option>
                    <option value="layered">Layered</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="deploymentEnvironment">Deployment Environment</label>
                <select id="deploymentEnvironment" name="deploymentEnvironment">
                    <option value="cloud">Cloud (AWS/Azure/GCP)</option>
                    <option value="on-premise">On-Premise</option>
                    <option value="hybrid">Hybrid</option>
                    <option value="containerized">Containerized (Docker/K8s)</option>
                </select>
            </div>
            
            <button type="submit" class="btn">🏗️ Generate Architecture</button>
            <a href="/" class="btn btn-secondary">← Back to Home</a>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Generating your Architecture with AI...</p>
        </div>
        
        <div id="result" class="result"></div>
    </div>
    
    <script>
        document.getElementById('archForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch('/bmad/api/architecture/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showResult('✅ Architecture created successfully!<br><br>' + 
                        '<strong>Document ID:</strong> ' + result.document_id + '<br>' +
                        '<strong>Status:</strong> ' + result.status + '<br><br>' +
                        '<strong>Content Preview:</strong><br>' +
                        '<pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">' +
                        result.content.substring(0, 500) + '...</pre>', 'success');
                } else {
                    showResult('❌ Error: ' + result.error, 'error');
                }
            } catch (error) {
                showResult('❌ Network error: ' + error.message, 'error');
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        });
        
        function showResult(message, type) {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = message;
            resultDiv.className = 'result ' + type;
            resultDiv.style.display = 'block';
        }
    </script>
</body>
</html>
        """
    
    def _get_story_form_html(self) -> str:
        """Get Story form HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create User Stories - BMAD</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        input, textarea, select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s ease;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #007bff;
        }
        textarea {
            height: 100px;
            resize: vertical;
        }
        .btn {
            background: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            transition: background 0.3s ease;
        }
        .btn:hover {
            background: #0056b3;
        }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover {
            background: #545b62;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 5px;
            display: none;
        }
        .result.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .result.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📖 Create User Stories</h1>
        
        <form id="storyForm">
            <div class="form-group">
                <label for="projectName">Project Name *</label>
                <input type="text" id="projectName" name="projectName" required>
            </div>
            
            <div class="form-group">
                <label for="architectureReference">Architecture Reference</label>
                <input type="text" id="architectureReference" name="architectureReference" 
                    placeholder="Reference to existing architecture or system design">
            </div>
            
            <div class="form-group">
                <label for="userPersonas">User Personas *</label>
                <textarea id="userPersonas" name="userPersonas" required
                    placeholder="Describe the target users and their roles..."></textarea>
            </div>
            
            <div class="form-group">
                <label for="businessValue">Business Value</label>
                <textarea id="businessValue" name="businessValue" 
                    placeholder="What business value will these stories deliver?"></textarea>
            </div>
            
            <div class="form-group">
                <label for="acceptanceCriteria">Acceptance Criteria</label>
                <textarea id="acceptanceCriteria" name="acceptanceCriteria" 
                    placeholder="General acceptance criteria or quality standards..."></textarea>
            </div>
            
            <div class="form-group">
                <label for="storyComplexity">Story Complexity</label>
                <select id="storyComplexity" name="storyComplexity">
                    <option value="simple">Simple (1-3 points)</option>
                    <option value="medium" selected>Medium (5-8 points)</option>
                    <option value="complex">Complex (8-13 points)</option>
                    <option value="epic">Epic (13+ points)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="sprintTimeline">Sprint Timeline</label>
                <input type="text" id="sprintTimeline" name="sprintTimeline" 
                    placeholder="e.g., 2-week sprints, 4 sprints total">
            </div>
            
            <button type="submit" class="btn">📖 Generate Stories</button>
            <a href="/" class="btn btn-secondary">← Back to Home</a>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Generating your User Stories with AI...</p>
        </div>
        
        <div id="result" class="result"></div>
    </div>
    
    <script>
        document.getElementById('storyForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            // Show loading
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch('/bmad/api/story/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showResult('✅ User Stories created successfully!<br><br>' + 
                        '<strong>Document ID:</strong> ' + result.document_id + '<br>' +
                        '<strong>Status:</strong> ' + result.status + '<br><br>' +
                        '<strong>Content Preview:</strong><br>' +
                        '<pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">' +
                        result.content.substring(0, 500) + '...</pre>', 'success');
                } else {
                    showResult('❌ Error: ' + result.error, 'error');
                }
            } catch (error) {
                showResult('❌ Network error: ' + error.message, 'error');
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        });
        
        function showResult(message, type) {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = message;
            resultDiv.className = 'result ' + type;
            resultDiv.style.display = 'block';
        }
    </script>
</body>
</html>
        """
    
    def _handle_prd_creation(self):
        """Handle PRD creation request."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            # Generate PRD content
            prd_content = self._generate_prd_content(data)
            
            result = {
                "status": "success",
                "document_id": f"prd_{int(datetime.utcnow().timestamp())}",
                "document_type": "PRD",
                "content": prd_content,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._send_json_response(200, result)
            
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})
    
    def _handle_architecture_creation(self):
        """Handle Architecture creation request."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            # Generate Architecture content
            arch_content = self._generate_architecture_content(data)
            
            result = {
                "status": "success",
                "document_id": f"arch_{int(datetime.utcnow().timestamp())}",
                "document_type": "Architecture",
                "content": arch_content,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._send_json_response(200, result)
            
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})
    
    def _handle_story_creation(self):
        """Handle Story creation request."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            # Generate Story content
            story_content = self._generate_story_content(data)
            
            result = {
                "status": "success",
                "document_id": f"story_{int(datetime.utcnow().timestamp())}",
                "document_type": "Story",
                "content": story_content,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._send_json_response(200, result)
            
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})
    
    def _generate_prd_content(self, data: Dict[str, Any]) -> str:
        """Generate PRD content."""
        return f"""
# Product Requirements Document: {data.get('projectName', 'Unknown Project')}

## 1. Project Overview
**Project Name:** {data.get('projectName', 'Unknown Project')}
**Description:** {data.get('projectDescription', 'No description provided')}
**Priority:** {data.get('priority', 'Medium')}
**Timeline:** {data.get('timeline', 'Not specified')}

## 2. Target Users
{data.get('targetUsers', 'Not specified')}

## 3. Business Goals
{data.get('businessGoals', 'Not specified')}

## 4. Technical Constraints
{data.get('technicalConstraints', 'Not specified')}

## 5. Functional Requirements
- [ ] Core functionality to be defined
- [ ] User interface requirements
- [ ] Integration requirements
- [ ] Performance requirements

## 6. Non-Functional Requirements
- [ ] Performance requirements
- [ ] Security requirements
- [ ] Scalability requirements
- [ ] Usability requirements

## 7. Success Criteria
- [ ] User acceptance criteria
- [ ] Performance benchmarks
- [ ] Quality metrics

## 8. Risks and Assumptions
- [ ] Technical risks
- [ ] Business risks
- [ ] Dependencies

---
*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} by BMAD Artifact Creator*
        """
    
    def _generate_architecture_content(self, data: Dict[str, Any]) -> str:
        """Generate Architecture content."""
        return f"""
# System Architecture: {data.get('projectName', 'Unknown Project')}

## 1. Architecture Overview
**Project Name:** {data.get('projectName', 'Unknown Project')}
**Architecture Style:** {data.get('architectureStyle', 'Microservices')}
**Deployment Environment:** {data.get('deploymentEnvironment', 'Cloud')}

## 2. PRD Reference
{data.get('prdReference', 'No PRD reference provided')}

## 3. Technical Constraints
{data.get('technicalConstraints', 'Not specified')}

## 4. Performance Requirements
{data.get('performanceRequirements', 'Not specified')}

## 5. Integration Points
{data.get('integrationPoints', 'Not specified')}

## 6. System Components
- [ ] Frontend Layer
- [ ] API Gateway
- [ ] Business Logic Layer
- [ ] Data Access Layer
- [ ] Database Layer
- [ ] External Integrations

## 7. Technology Stack
- [ ] Frontend: To be determined
- [ ] Backend: To be determined
- [ ] Database: To be determined
- [ ] Infrastructure: To be determined

## 8. Architecture Patterns
- [ ] Design patterns to be applied
- [ ] Architectural principles
- [ ] Quality attributes

## 9. Deployment Architecture
- [ ] Environment setup
- [ ] Deployment strategy
- [ ] Monitoring and logging

---
*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} by BMAD Artifact Creator*
        """
    
    def _generate_story_content(self, data: Dict[str, Any]) -> str:
        """Generate Story content."""
        return f"""
# User Stories: {data.get('projectName', 'Unknown Project')}

## 1. Project Overview
**Project Name:** {data.get('projectName', 'Unknown Project')}
**Story Complexity:** {data.get('storyComplexity', 'Medium')}
**Sprint Timeline:** {data.get('sprintTimeline', 'Not specified')}

## 2. Architecture Reference
{data.get('architectureReference', 'No architecture reference provided')}

## 3. User Personas
{data.get('userPersonas', 'Not specified')}

## 4. Business Value
{data.get('businessValue', 'Not specified')}

## 5. Acceptance Criteria
{data.get('acceptanceCriteria', 'Not specified')}

## 6. User Stories

### Epic 1: Core Functionality
**As a** user  
**I want to** access core functionality  
**So that** I can achieve my primary goals  

**Acceptance Criteria:**
- [ ] User can access the main features
- [ ] System responds within acceptable time
- [ ] Error handling is appropriate

**Story Points:** 5  
**Priority:** High  

### Epic 2: User Management
**As a** user  
**I want to** manage my account  
**So that** I can personalize my experience  

**Acceptance Criteria:**
- [ ] User can create account
- [ ] User can update profile
- [ ] User can manage preferences

**Story Points:** 8  
**Priority:** Medium  

## 7. Sprint Planning
- [ ] Sprint 1: Epic 1 - Core Functionality
- [ ] Sprint 2: Epic 2 - User Management
- [ ] Sprint 3: Additional features
- [ ] Sprint 4: Testing and refinement

## 8. Definition of Done
- [ ] Code is written and tested
- [ ] Documentation is updated
- [ ] Code review is completed
- [ ] Acceptance criteria are met

---
*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} by BMAD Artifact Creator*
        """
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8002), BMADWebHandler)
    print('BMAD Web Interface running on port 8002')
    server.serve_forever()
