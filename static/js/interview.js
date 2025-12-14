/**
 * SME Interview System - Frontend JavaScript
 * Push-to-Talk style voice input for older SMEs
 * 
 * States: idle → recording → editing → sending → playing → idle
 * 
 * Design: Like a tape recorder, not a chat app.
 * User controls every step. No rushing.
 */

class InterviewController {
    constructor() {
        this.sessionId = null;
        this.recognition = null;
        
        // State machine: 'idle' | 'recording' | 'editing' | 'sending' | 'playing'
        this.state = 'idle';
        this.transcript = '';
        
        // Voice settings and cost tracking
        this.voicePreset = 'premium_female';
        this.speechRate = 0.95;
        this.sessionCost = 0;
        
        // Recording timer
        this.recordingStartTime = null;
        this.recordingTimer = null;
        
        this.audioPlayer = document.getElementById('audioPlayer');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        
        this.initSpeechRecognition();
        this.initEventListeners();
    }
    
    /**
     * Initialize Web Speech API
     * KEY: continuous=true, interimResults=true for PTT style
     */
    initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('Speech recognition not supported');
            this.showBrowserWarning();
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;          // Don't stop on pause
        this.recognition.interimResults = true;      // Show text as they speak
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
        
        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const text = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += text + ' ';
                } else {
                    interimTranscript += text;
                }
            }
            
            // Accumulate final transcript
            if (finalTranscript) {
                this.transcript += finalTranscript;
            }
            
            // Update display with accumulated + interim
            this.updateTranscriptDisplay(this.transcript + interimTranscript);
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            
            // Ignore no-speech errors - user is just pausing to think
            if (event.error === 'no-speech') {
                return;
            }
            
            if (event.error === 'audio-capture') {
                this.setStatus('error', '❌ Microphone not available. Check permissions.');
            } else if (event.error === 'not-allowed') {
                this.setStatus('error', '❌ Microphone access denied. Please enable permissions.');
            } else if (event.error !== 'aborted') {
                this.setStatus('error', `❌ Error: ${event.error}`);
            }
        };
        
        this.recognition.onend = () => {
            // If still in recording state, restart (handles browser timeouts)
            if (this.state === 'recording') {
                try {
                    this.recognition.start();
                } catch (e) {
                    console.log('Could not restart recognition:', e);
                }
            }
        };
    }
    
    /**
     * Show warning for unsupported browsers
     */
    showBrowserWarning() {
        const startBtn = document.getElementById('startRecordingBtn');
        if (startBtn) {
            startBtn.innerHTML = `
                <span class="button-icon">⌨️</span>
                <span class="button-text">TYPE YOUR RESPONSE</span>
                <span class="button-hint">Voice not supported - type below</span>
            `;
            startBtn.classList.remove('record-button');
            startBtn.classList.add('secondary-button');
        }
        
        // Make textarea always editable
        const textarea = document.getElementById('transcriptArea');
        if (textarea) {
            textarea.readOnly = false;
            textarea.placeholder = 'Type your response here...';
        }
    }
    
    /**
     * Initialize all event listeners
     */
    initEventListeners() {
        // Start session button
        document.getElementById('startButton').addEventListener('click', () => this.startSession());
        
        // PTT buttons
        document.getElementById('startRecordingBtn').addEventListener('click', () => this.startRecording());
        document.getElementById('stopRecordingBtn').addEventListener('click', () => this.stopRecording());
        document.getElementById('recordMoreBtn').addEventListener('click', () => this.startRecording());
        document.getElementById('sendMessageBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('skipAudioBtn').addEventListener('click', () => this.skipAudio());
        
        // End interview button
        document.getElementById('endButton').addEventListener('click', () => this.endSession());
        
        // Audio player events
        this.audioPlayer.addEventListener('ended', () => {
            this.setState('idle');
        });
        
        this.audioPlayer.addEventListener('error', (e) => {
            console.error('Audio playback error:', e);
            this.setState('idle');
        });
        
        // Enter key to start session
        document.getElementById('expertNameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.startSession();
        });
        
        // Ctrl+Enter to send from textarea
        document.getElementById('transcriptArea').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey && this.state === 'editing') {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Voice tier selection
        document.querySelectorAll('input[name="voiceTier"]').forEach(radio => {
            radio.addEventListener('change', () => this.updateVoiceSelection());
        });
        document.querySelectorAll('input[name="voiceGender"]').forEach(radio => {
            radio.addEventListener('change', () => this.updateVoiceSelection());
        });
        
        // Speech rate slider
        document.getElementById('speechRate').addEventListener('input', (e) => {
            document.getElementById('speechRateValue').textContent = e.target.value + 'x';
        });
        
        // Initialize voice selection state (Premium doesn't support rate)
        this.updateVoiceSelection();
    }
    
    /**
     * Update voice selection UI based on tier
     */
    updateVoiceSelection() {
        const tier = document.querySelector('input[name="voiceTier"]:checked').value;
        const rateSlider = document.getElementById('speechRate');
        const rateWarning = document.getElementById('rateNotSupported');
        
        // Premium tier doesn't support rate adjustment
        if (tier === 'premium') {
            rateSlider.disabled = true;
            rateSlider.value = 1.0;
            document.getElementById('speechRateValue').textContent = '1.0x';
            rateWarning.classList.remove('hidden');
        } else {
            rateSlider.disabled = false;
            rateWarning.classList.add('hidden');
        }
    }
    
    /**
     * Set the UI state - controls which buttons are visible
     */
    setState(newState) {
        this.state = newState;
        
        // Hide all button groups
        document.querySelectorAll('.button-group').forEach(g => g.classList.add('hidden'));
        
        // Show the relevant button group
        const stateMap = {
            'idle': 'idleButtons',
            'recording': 'recordingButtons',
            'editing': 'editingButtons',
            'sending': 'sendingButtons',
            'playing': 'playingButtons'
        };
        
        const buttonGroup = document.getElementById(stateMap[newState]);
        if (buttonGroup) {
            buttonGroup.classList.remove('hidden');
        }
        
        // Update transcript area styling
        const textarea = document.getElementById('transcriptArea');
        const label = document.getElementById('transcriptLabel');
        textarea.classList.remove('recording', 'editable');
        
        switch (newState) {
            case 'idle':
                textarea.readOnly = true;
                textarea.placeholder = "Click 'Start Recording' and speak your response...";
                label.textContent = 'Your response will appear here...';
                this.setStatus('tip', '💡 Tip: Take your time. Click Stop when you\'re done talking.');
                break;
                
            case 'recording':
                textarea.classList.add('recording');
                textarea.readOnly = true;
                label.textContent = 'Recording your response...';
                this.setStatus('recording', '🎤 RECORDING - Take your time. Pause if you need to think.');
                break;
                
            case 'editing':
                textarea.classList.add('editable');
                textarea.readOnly = false;
                textarea.focus();
                label.textContent = 'Review and edit your response:';
                this.setStatus('info', '✏️ Review your message. Edit if needed, then click Send.');
                break;
                
            case 'sending':
                textarea.readOnly = true;
                label.textContent = 'Sending...';
                this.setStatus('info', '⏳ Sending to Claude...');
                break;
                
            case 'playing':
                textarea.readOnly = true;
                label.textContent = 'Interviewer is responding...';
                this.setStatus('success', '🔊 Playing response... Click to skip.');
                break;
        }
    }
    
    /**
     * Update the status bar
     */
    setStatus(type, message) {
        const statusBar = document.getElementById('statusBar');
        statusBar.className = 'status-bar ' + type;
        document.getElementById('statusText').textContent = message;
    }
    
    /**
     * Update transcript display
     */
    updateTranscriptDisplay(text) {
        document.getElementById('transcriptArea').value = text;
    }
    
    /**
     * Start recording
     */
    startRecording() {
        if (!this.recognition) {
            // Fallback: just enable typing
            this.setState('editing');
            return;
        }
        
        // Keep existing text if recording more
        this.transcript = document.getElementById('transcriptArea').value || '';
        
        // Start timer
        this.recordingStartTime = Date.now();
        this.startRecordingTimer();
        
        // Start recognition
        try {
            this.recognition.start();
            this.setState('recording');
        } catch (error) {
            console.error('Failed to start recognition:', error);
            this.setStatus('error', '❌ Could not start microphone. Try again.');
        }
    }
    
    /**
     * Stop recording
     */
    stopRecording() {
        if (this.recognition) {
            try {
                this.recognition.stop();
            } catch (e) {
                console.log('Recognition already stopped');
            }
        }
        
        this.stopRecordingTimer();
        
        // Get the final transcript
        this.transcript = document.getElementById('transcriptArea').value;
        
        if (this.transcript.trim()) {
            this.setState('editing');
        } else {
            this.setState('idle');
            this.setStatus('tip', '💡 No speech detected. Click Start Recording to try again.');
        }
    }
    
    /**
     * Start the recording duration timer
     */
    startRecordingTimer() {
        const timerEl = document.getElementById('recordingTime');
        timerEl.textContent = '0:00';
        
        this.recordingTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const mins = Math.floor(elapsed / 60);
            const secs = elapsed % 60;
            timerEl.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
        }, 1000);
    }
    
    /**
     * Stop the recording timer
     */
    stopRecordingTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }
    
    /**
     * Start a new interview session
     */
    async startSession() {
        const nameInput = document.getElementById('expertNameInput');
        const callsignInput = document.getElementById('expertCallsign');
        const topicsInput = document.getElementById('topicsInput');
        
        // Get voice settings
        const tier = document.querySelector('input[name="voiceTier"]:checked').value;
        const gender = document.querySelector('input[name="voiceGender"]:checked').value;
        const speechRate = parseFloat(document.getElementById('speechRate').value);
        
        const name = nameInput.value.trim();
        const callsign = callsignInput.value.trim();
        const topicsText = topicsInput.value.trim();
        
        // Build voice preset key (e.g., "premium_female")
        this.voicePreset = `${tier}_${gender}`;
        this.speechRate = speechRate;
        
        if (!name) {
            nameInput.focus();
            nameInput.classList.add('error');
            return;
        }
        
        const topics = topicsText ? topicsText.split(',').map(t => t.trim()).filter(t => t) : null;
        
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    expert_name: name, 
                    expert_callsign: callsign || null,
                    topics: topics,
                    voice_preset: this.voicePreset,
                    speech_rate: this.speechRate
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to start session');
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            this.sessionCost = data.session_cost || 0;
            
            // Update UI
            document.getElementById('startForm').classList.add('hidden');
            document.getElementById('chatInterface').classList.remove('hidden');
            document.getElementById('sessionInfo').classList.remove('hidden');
            document.getElementById('expertName').textContent = callsign ? `${name} (${callsign})` : name;
            
            // Show voice info and cost
            const tierEmojis = { budget: '💰', standard: '⭐', premium: '✨' };
            const genderEmojis = { female: '👩', male: '👨' };
            const voiceLabel = `${tierEmojis[tier] || ''} ${tier.charAt(0).toUpperCase() + tier.slice(1)} ${genderEmojis[gender] || ''}`;
            document.getElementById('voiceQuality').textContent = voiceLabel;
            this.updateCostDisplay();
            
            // Add greeting and play audio
            this.addMessage('assistant', data.greeting);
            
            if (data.audio_url) {
                this.playAudio(data.audio_url);
            } else {
                this.setState('idle');
            }
            
            console.log('Session started:', this.sessionId);
            
        } catch (error) {
            console.error('Failed to start session:', error);
            alert('Failed to start interview: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Send message to Claude
     */
    async sendMessage() {
        const text = document.getElementById('transcriptArea').value.trim();
        if (!text || !this.sessionId) return;
        
        this.setState('sending');
        this.addMessage('user', text);
        
        // Clear transcript for next input
        document.getElementById('transcriptArea').value = '';
        this.transcript = '';
        
        try {
            const response = await fetch('/api/interview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    text: text
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to get response');
            }
            
            const data = await response.json();
            
            // Update cost tracking
            if (data.session_cost !== undefined) {
                this.sessionCost = data.session_cost;
                this.updateCostDisplay();
            }
            
            // Add response message
            this.addMessage('assistant', data.response_text);
            this.updateMessageCount(data.message_count);
            
            if (data.extraction_triggered) {
                console.log('Knowledge extraction triggered');
            }
            
            // Play response audio
            if (data.audio_url) {
                this.playAudio(data.audio_url);
            } else {
                this.setState('idle');
            }
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.addMessage('system', 'Error: ' + error.message);
            this.setStatus('error', '❌ Failed to send. Please try again.');
            this.setState('editing');
            // Restore the text so user can retry
            document.getElementById('transcriptArea').value = text;
            this.transcript = text;
        }
    }
    
    /**
     * Update the session cost display
     */
    updateCostDisplay() {
        const costEl = document.getElementById('sessionCost');
        if (costEl) {
            costEl.textContent = `$${this.sessionCost.toFixed(4)}`;
        }
    }
    
    /**
     * Play audio response
     */
    playAudio(url) {
        if (!url) {
            this.setState('idle');
            return;
        }
        
        this.setState('playing');
        this.audioPlayer.src = url;
        this.audioPlayer.play().catch(error => {
            console.error('Failed to play audio:', error);
            this.setState('idle');
        });
    }
    
    /**
     * Skip audio playback
     */
    skipAudio() {
        this.audioPlayer.pause();
        this.audioPlayer.currentTime = 0;
        this.setState('idle');
    }
    
    /**
     * Add message to chat display
     */
    addMessage(role, content) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
        
        let avatar, label;
        switch (role) {
            case 'user':
                avatar = '👤';
                label = 'You';
                break;
            case 'assistant':
                avatar = '🤖';
                label = 'Interviewer';
                break;
            case 'system':
                avatar = 'ℹ️';
                label = 'System';
                break;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-label">${label}</span>
                    <span class="message-time">${timeStr}</span>
                </div>
                <div class="message-text">${this.escapeHtml(content)}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    /**
     * Update message count display
     */
    updateMessageCount(count) {
        document.getElementById('messageCount').textContent = `${count} exchanges`;
    }
    
    /**
     * Show/hide loading overlay
     */
    showLoading(show) {
        if (show) {
            this.loadingOverlay.classList.remove('hidden');
        } else {
            this.loadingOverlay.classList.add('hidden');
        }
    }
    
    /**
     * End the interview session
     */
    async endSession() {
        if (!confirm('End this interview? A summary will be generated.')) {
            return;
        }
        
        if (this.recognition) {
            try { this.recognition.stop(); } catch (e) {}
        }
        this.stopRecordingTimer();
        this.showLoading(true);
        
        try {
            const response = await fetch(`/api/sessions/${this.sessionId}/end`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to end session');
            }
            
            const data = await response.json();
            
            this.addMessage('system', `Interview completed! ${data.message_count} exchanges recorded over ${this.formatDuration(data.duration_seconds)}.`);
            this.addMessage('system', `View transcript: ${data.transcript_url}`);
            
            // Disable all controls
            document.getElementById('startRecordingBtn').disabled = true;
            document.getElementById('stopRecordingBtn').disabled = true;
            document.getElementById('recordMoreBtn').disabled = true;
            document.getElementById('sendMessageBtn').disabled = true;
            document.getElementById('endButton').disabled = true;
            document.getElementById('transcriptArea').disabled = true;
            
            this.setStatus('success', '✅ Interview completed successfully!');
            
        } catch (error) {
            console.error('Failed to end session:', error);
            this.addMessage('system', 'Error ending session: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Format duration in seconds to readable string
     */
    formatDuration(seconds) {
        if (seconds < 60) return `${seconds} seconds`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return `${hours}h ${remainingMinutes}m`;
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.interviewController = new InterviewController();
    console.log('Interview controller initialized (Push-to-Talk mode)');
});
