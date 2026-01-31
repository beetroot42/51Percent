/**
 * 陪审团辩论逻辑模块
 */

const Deliberation = {
    sessionId: null,
    eventSource: null,
    jurors: [], // { id, name, stance, x, y }
    round: 0,
    totalRounds: 4,
    notesRemaining: 3,

    // 初始化
    init(sessionId) {
        this.sessionId = sessionId;
        this.renderRing();
        this.startSSE();
        this.bindEvents();
    },

    // 绑定交互事件
    bindEvents() {
        document.getElementById('open-note-btn').addEventListener('click', () => {
            this.showNoteModal();
        });

        document.getElementById('cancel-note-btn').addEventListener('click', () => {
            document.getElementById('note-modal').classList.add('hidden');
        });

        document.getElementById('submit-note-btn').addEventListener('click', () => {
            this.submitNote();
        });

        document.getElementById('skip-deliberation-btn').addEventListener('click', () => {
            if (confirm('Are you sure you want to skip the remaining deliberation?')) {
                skipDeliberation(this.sessionId).then(() => {
                    if (this.eventSource) this.eventSource.close();
                    if (typeof enterVerdict === 'function') {
                        enterVerdict();
                    } else {
                        location.reload();
                    }
                }).catch(console.error);
            }
        });
    },

    // 渲染陪审员座位 (半圆)
    renderRing() {
        // 先获取陪审员列表
        getJurors(this.sessionId).then(jurors => {
            this.jurors = jurors;
            const container = document.getElementById('deliberation-ring');
            container.innerHTML = '';
            
            const count = jurors.length;
            const radius = 120; // 半径 px
            const angleStep = 180 / (count + 1); // 均匀分布

            jurors.forEach((juror, index) => {
                const angle = 180 - (index + 1) * angleStep; // 180 -> 0
                const rad = (angle * Math.PI) / 180;
                
                // 计算位置 (中心点 x=50%, bottom y=0)
                // x = cos(angle) * r
                // y = sin(angle) * r
                
                // CSS 中 transform: translate(x, -y)
                const x = Math.cos(rad) * radius;
                const y = Math.sin(rad) * radius;

                const seat = document.createElement('div');
                seat.className = 'juror-seat';
                seat.id = `seat-${juror.id}`;
                seat.dataset.id = juror.id;
                
                // Desktop: absolute positioning along arc
                if (window.innerWidth > 768) {
                    // left: 50% + x
                    seat.style.left = `calc(50% - 40px + ${x}px)`; // 40px is half width
                    seat.style.bottom = `${y}px`;
                }

                const avatar = document.createElement('div');
                avatar.className = 'avatar';
                avatar.textContent = (juror.name && juror.name[0]) ? juror.name[0] : '?';

                const nameSpan = document.createElement('span');
                nameSpan.className = 'name';
                nameSpan.textContent = juror.name || juror.id;

                seat.appendChild(avatar);
                seat.appendChild(nameSpan);
                
                container.appendChild(seat);
            });

            this.updateOpinionScale(jurors);
        });
    },

    // SSE 连接
    startSSE() {
        if (this.eventSource) this.eventSource.close();

        // Start endpoint triggers the backend process, then we listen to stream
        startDeliberation(this.sessionId).then(() => {
            const url = `${API_BASE}/deliberation/stream?session_id=${this.sessionId}`;
            console.log('Connecting SSE:', url);
            
            this.eventSource = new EventSource(url);

            this.eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleEvent(data); // Generic handler if backend sends simple JSON
            };

            // Custom event types
            this.eventSource.addEventListener('debate.start', (e) => {
                const data = JSON.parse(e.data);
                console.log('Debate Started:', data);
                this.totalRounds = data.total_rounds;
                this.updateStatus();
            });

            this.eventSource.addEventListener('round.start', (e) => {
                const data = JSON.parse(e.data);
                this.round = data.round;
                this.updateStatus();
                this.highlightSpeakers(data.leader_id, data.responder_ids);
                this.appendSystemMsg(`Round ${data.round} begins.`);
            });

            this.eventSource.addEventListener('speech.chunk', (e) => {
                const data = JSON.parse(e.data);
                this.renderSpeechChunk(data);
            });

            this.eventSource.addEventListener('speech.end', (e) => {
                const data = JSON.parse(e.data);
                this.finalizeSpeech(data);
                if (data.stance_deltas) {
                    this.visualizeStanceShifts(data.stance_deltas);
                }
            });

            this.eventSource.addEventListener('note.window', (e) => {
                const data = JSON.parse(e.data);
                this.notesRemaining = data.notes_remaining;
                this.updateNoteBtn();
                // Optionally auto-open or just enable button
            });
            
            this.eventSource.addEventListener('note.received', (e) => {
                const data = JSON.parse(e.data);
                this.notesRemaining = data.notes_remaining;
                this.updateNoteBtn();
                this.appendSystemMsg(`Note passed to ${data.target_id}.`);
                document.getElementById('note-modal').classList.add('hidden');
            });

            this.eventSource.addEventListener('debate.end', (e) => {
                console.log('Debate Ended');
                this.eventSource.close();
                // Transition to Verdict
                setTimeout(() => {
                    if (typeof enterVerdict === 'function') {
                        enterVerdict();
                    } else {
                        setPhase('verdict', this.sessionId).then(() => {
                            location.reload();
                        });
                    }
                }, 3000);
            });

            this.eventSource.onerror = (e) => {
                console.error('SSE Error:', e);
                // Simple reconnect logic is built-in to EventSource, 
                // but if we need manual logic or error handling:
                // this.eventSource.close();
            };
        });
    },

    handleEvent(data) {
        // Fallback for generic messages
    },

    // UI 更新
    updateStatus() {
        document.getElementById('deliberation-round').textContent = `Round ${this.round}/${this.totalRounds}`;
    },

    highlightSpeakers(leaderId, responderIds) {
        // Reset all
        document.querySelectorAll('.juror-seat').forEach(el => {
            el.classList.remove('speaking', 'responding', 'silent');
            el.classList.add('silent');
        });

        // Highlight Leader
        const leaderEl = document.getElementById(`seat-${leaderId}`);
        if (leaderEl) {
            leaderEl.classList.remove('silent');
            leaderEl.classList.add('speaking');
        }

        // Highlight Responders
        responderIds.forEach(id => {
            const el = document.getElementById(`seat-${id}`);
            if (el) {
                el.classList.remove('silent');
                el.classList.add('responding');
            }
        });
    },

    chatBuffer: {}, // { speakerId: "current text..." }

    renderSpeechChunk(data) {
        // Find existing message bubble or create new
        // Ideally we stream into a single bubble for the current speaker
        const container = document.getElementById('deliberation-transcript');
        let bubbleId = `speech-${this.round}-${data.speaker_id}`;
        let bubble = document.getElementById(bubbleId);

        if (!bubble) {
            bubble = document.createElement('div');
            bubble.id = bubbleId;
            bubble.className = `transcript-entry ${data.role}`;
            const label = document.createElement('span');
            label.className = 'speaker-label';
            label.textContent = data.speaker_id;

            const textSpan = document.createElement('span');
            textSpan.className = 'text';

            bubble.appendChild(label);
            bubble.appendChild(textSpan);
            container.appendChild(bubble);
            // Auto scroll
            const scrollContainer = document.getElementById('deliberation-transcript-container');
            scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }

        const textSpan = bubble.querySelector('.text');
        textSpan.textContent += data.text;
        
        // Auto scroll
        const scrollContainer = document.getElementById('deliberation-transcript-container');
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
    },

    finalizeSpeech(data) {
        // Ensure full text is correct (in case of dropped chunks)
        const bubbleId = `speech-${data.round}-${data.speaker_id}`;
        let bubble = document.getElementById(bubbleId);
        if (bubble) {
            bubble.querySelector('.text').textContent = data.full_text;
        }
    },

    visualizeStanceShifts(deltas) {
        Object.keys(deltas).forEach(jurorId => {
            const delta = deltas[jurorId];
            if (delta === 0) return;

            const seat = document.getElementById(`seat-${jurorId}`);
            if (seat) {
                const className = delta > 0 ? 'stance-shift-guilty' : 'stance-shift-not-guilty';
                seat.classList.add(className);
                setTimeout(() => seat.classList.remove(className), 1000);
            }
        });
        
        // Update local state and scale
        this.jurors.forEach(j => {
            if (deltas[j.id]) j.stance = Math.max(0, Math.min(100, j.stance + deltas[j.id]));
        });
        this.updateOpinionScale(this.jurors);
    },

    updateOpinionScale(jurors) {
        if (!jurors || jurors.length === 0) return;
        
        const avgStance = jurors.reduce((sum, j) => sum + j.stance, 0) / jurors.length;
        const indicator = document.getElementById('opinion-indicator');
        const meter = document.getElementById('opinion-scale');
        
        // 0 = Not Guilty (Right in CSS gradient? No, CSS gradient: Red(0) -> Green(100))
        // Wait: CSS is `linear-gradient(90deg, #e94560 0%, #333 50%, #4ecca3 100%)`
        // 0% is Red (Guilty), 100% is Green (Not Guilty).
        // Stance: 0 = Not Guilty, 100 = Guilty.
        // So Stance 100 should be LEFT (0%). Stance 0 should be RIGHT (100%).
        // Position = 100 - stance.
        
        indicator.style.left = `${100 - avgStance}%`;
        if (meter) {
            meter.setAttribute('aria-valuenow', Math.round(avgStance).toString());
            const label = avgStance > 50 ? `Guilty ${Math.round(avgStance)}` : `Not guilty ${Math.round(100 - avgStance)}`;
            meter.setAttribute('aria-valuetext', label);
        }
    },

    appendSystemMsg(text) {
        const container = document.getElementById('deliberation-transcript');
        const msg = document.createElement('div');
        msg.className = 'transcript-note';
        msg.textContent = text;
        container.appendChild(msg);
    },

    // 纸条功能
    updateNoteBtn() {
        document.getElementById('notes-remaining').textContent = this.notesRemaining;
        const btn = document.getElementById('open-note-btn');
        btn.disabled = this.notesRemaining <= 0;
    },

    showNoteModal() {
        const modal = document.getElementById('note-modal');
        const selector = document.getElementById('note-target-selector');
        selector.innerHTML = '';

        this.jurors.forEach(j => {
            const opt = document.createElement('button');
            opt.type = 'button';
            opt.className = 'note-target-option';
            opt.textContent = j.name;
            opt.dataset.id = j.id;
            opt.setAttribute('aria-pressed', 'false');
            opt.addEventListener('click', () => {
                document.querySelectorAll('.note-target-option').forEach(o => {
                    o.classList.remove('selected');
                    o.setAttribute('aria-pressed', 'false');
                });
                opt.classList.add('selected');
                opt.setAttribute('aria-pressed', 'true');
            });
            selector.appendChild(opt);
        });

        modal.classList.remove('hidden');
    },

    submitNote() {
        const selected = document.querySelector('.note-target-option.selected');
        const content = document.getElementById('note-content').value.trim();

        if (!selected) {
            if (typeof showError === 'function') {
                showError('Please select a juror.');
            } else {
                alert('Please select a juror.');
            }
            return;
        }
        if (!content) {
            if (typeof showError === 'function') {
                showError('Please enter a message.');
            } else {
                alert('Please enter a message.');
            }
            return;
        }

        const targetId = selected.dataset.id;
        // Generate idempotency key
        const key = `note-${this.round}-${Date.now()}`;

        submitNote(this.sessionId, targetId, content, key)
            .then(() => {
                // Success handled by SSE event 'note.received' usually
                // But we can optimistically close
                document.getElementById('note-modal').classList.add('hidden');
                document.getElementById('note-content').value = '';
            })
            .catch(err => {
                const message = `Failed to send note: ${err.message}`;
                if (typeof showError === 'function') {
                    showError(message);
                } else {
                    alert(message);
                }
            });
    }
};

// Export to global scope
window.Deliberation = Deliberation;
