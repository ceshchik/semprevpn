/**
 * General Intelligence Company — Interactive 4K Video Player & Literary Experience
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- Video Player Elements ---
  const video = document.getElementById('main-video');
  const videoContainer = document.getElementById('video-container');
  const bigPlayBtn = document.getElementById('big-play-btn');
  const playPauseBtn = document.getElementById('play-pause-btn');
  const playIcon = document.getElementById('play-icon');
  const pauseIcon = document.getElementById('pause-icon');
  
  const scrubberContainer = document.getElementById('scrubber-container');
  const scrubberProgress = document.getElementById('scrubber-progress');
  const scrubberHandle = document.getElementById('scrubber-handle');
  const scrubberTooltip = document.getElementById('scrubber-tooltip');
  
  const currentTimeEl = document.getElementById('current-time');
  const durationTimeEl = document.getElementById('duration-time');
  
  const muteBtn = document.getElementById('mute-btn');
  const volumeSlider = document.getElementById('volume-slider');
  const volumeHighIcon = document.getElementById('volume-high-icon');
  const volumeMutedIcon = document.getElementById('volume-muted-icon');
  
  const qualitySelect = document.getElementById('quality-select');
  const speedSelect = document.getElementById('speed-select');
  const ccBtn = document.getElementById('cc-btn');
  const subtitlesOverlay = document.getElementById('subtitles-overlay');
  
  const theaterBtn = document.getElementById('theater-btn');
  const fullscreenBtn = document.getElementById('fullscreen-btn');
  
  const chapterCards = document.querySelectorAll('.chapter-card-btn');
  const transcriptEntries = document.querySelectorAll('.transcript-entry');
  
  // Format seconds to mm:ss
  function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  // Set total duration once metadata loads
  video.addEventListener('loadedmetadata', () => {
    durationTimeEl.textContent = formatTime(video.duration || 300);
  });

  // Toggle Play / Pause
  function togglePlay() {
    if (video.paused || video.ended) {
      video.play().catch(err => console.log('Playback error:', err));
    } else {
      video.pause();
    }
  }

  video.addEventListener('play', () => {
    bigPlayBtn.style.opacity = '0';
    bigPlayBtn.style.pointerEvents = 'none';
    playIcon.style.display = 'none';
    pauseIcon.style.display = 'block';
  });

  video.addEventListener('pause', () => {
    bigPlayBtn.style.opacity = '1';
    bigPlayBtn.style.pointerEvents = 'auto';
    playIcon.style.display = 'block';
    pauseIcon.style.display = 'none';
  });

  video.addEventListener('click', togglePlay);
  bigPlayBtn.addEventListener('click', togglePlay);
  playPauseBtn.addEventListener('click', togglePlay);

  // Keyboard shortcut: Spacebar for play/pause
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      togglePlay();
    }
  });

  // Time Update & Scrubber Progress
  video.addEventListener('timeupdate', () => {
    const current = video.currentTime;
    const duration = video.duration || 300;
    const percent = (current / duration) * 100;
    
    scrubberProgress.style.width = `${percent}%`;
    currentTimeEl.textContent = formatTime(current);

    // Update active chapter button
    const currentChapterIdx = Math.min(4, Math.floor(current / 60));
    chapterCards.forEach((card, idx) => {
      if (idx === currentChapterIdx) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });

    // Synchronize Literary Transcript
    transcriptEntries.forEach((entry) => {
      const start = parseFloat(entry.dataset.start);
      const end = parseFloat(entry.dataset.end);
      if (current >= start && current < end) {
        entry.classList.add('active');
        if (subtitlesEnabled) {
          subtitlesOverlay.textContent = entry.querySelector('.transcript-text').textContent;
          subtitlesOverlay.classList.add('active');
        }
      } else {
        entry.classList.remove('active');
      }
    });

    if (subtitlesEnabled && (current > 298 || !document.querySelector('.transcript-entry.active'))) {
      subtitlesOverlay.classList.remove('active');
    }
  });

  // Scrubber Click & Drag
  let isScrubbing = false;

  function scrub(e) {
    const rect = scrubberContainer.getBoundingClientRect();
    const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const duration = video.duration || 300;
    video.currentTime = pos * duration;
    scrubberProgress.style.width = `${pos * 100}%`;
  }

  scrubberContainer.addEventListener('mousedown', (e) => {
    isScrubbing = true;
    scrub(e);
  });

  window.addEventListener('mousemove', (e) => {
    if (isScrubbing) {
      scrub(e);
    }
    // Hover tooltip
    const rect = scrubberContainer.getBoundingClientRect();
    if (e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top - 20 && e.clientY <= rect.bottom + 10) {
      const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      const duration = video.duration || 300;
      scrubberTooltip.style.left = `${pos * 100}%`;
      scrubberTooltip.textContent = formatTime(pos * duration);
      scrubberTooltip.style.opacity = '1';
    } else {
      scrubberTooltip.style.opacity = '0';
    }
  });

  window.addEventListener('mouseup', () => {
    isScrubbing = false;
  });

  // Volume & Mute Controls
  volumeSlider.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    video.volume = val;
    video.muted = (val === 0);
    updateVolumeIcon();
  });

  muteBtn.addEventListener('click', () => {
    video.muted = !video.muted;
    if (video.muted) {
      volumeSlider.value = 0;
    } else {
      volumeSlider.value = video.volume || 1;
    }
    updateVolumeIcon();
  });

  function updateVolumeIcon() {
    if (video.muted || video.volume === 0) {
      volumeHighIcon.style.display = 'none';
      volumeMutedIcon.style.display = 'block';
    } else {
      volumeHighIcon.style.display = 'block';
      volumeMutedIcon.style.display = 'none';
    }
  }

  // Playback Speed
  speedSelect.addEventListener('change', (e) => {
    video.playbackRate = parseFloat(e.target.value);
  });

  // Quality Selector (4K UHD vs 1080p FHD)
  qualitySelect.addEventListener('change', (e) => {
    const newQuality = e.target.value;
    const currentTime = video.currentTime;
    const isPaused = video.paused;

    const sourceEl = video.querySelector('source');
    if (newQuality === '4k') {
      sourceEl.src = 'assets/video/film_4k_5min.mp4';
      document.querySelector('.video-badge-4k span').textContent = '4K UHD 2160p';
    } else {
      sourceEl.src = 'assets/video/film_1080p_5min.mp4';
      document.querySelector('.video-badge-4k span').textContent = '1080p FHD';
    }

    video.load();
    video.currentTime = currentTime;
    if (!isPaused) {
      video.play().catch(err => console.log('Resume error:', err));
    }
  });

  // Subtitles / CC Toggle
  let subtitlesEnabled = true;
  ccBtn.addEventListener('click', () => {
    subtitlesEnabled = !subtitlesEnabled;
    if (subtitlesEnabled) {
      ccBtn.style.color = '#41a1cf';
      subtitlesOverlay.style.display = 'block';
    } else {
      ccBtn.style.color = '#dee2de';
      subtitlesOverlay.classList.remove('active');
      subtitlesOverlay.style.display = 'none';
    }
  });
  // Default CC active color
  ccBtn.style.color = '#41a1cf';

  // Theater Mode
  theaterBtn.addEventListener('click', () => {
    videoContainer.classList.toggle('theater-mode');
  });

  // Fullscreen
  fullscreenBtn.addEventListener('click', () => {
    if (!document.fullscreenElement) {
      videoContainer.requestFullscreen().catch(err => {
        alert(`Error attempting fullscreen: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  });

  // Chapter Cards Click to Seek
  chapterCards.forEach((card) => {
    card.addEventListener('click', () => {
      const targetTime = parseFloat(card.dataset.time);
      video.currentTime = targetTime;
      if (video.paused) {
        video.play();
      }
    });
  });

  // Transcript Entry Click to Seek
  transcriptEntries.forEach((entry) => {
    entry.addEventListener('click', () => {
      const start = parseFloat(entry.dataset.start);
      video.currentTime = start;
      if (video.paused) {
        video.play();
      }
    });
  });

  // --- Cookie Banner Logic ---
  const cookieBanner = document.getElementById('cookie-banner');
  const cookieAcceptBtn = document.getElementById('cookie-accept');
  const cookieDeclineBtn = document.getElementById('cookie-decline');

  if (localStorage.getItem('gic_cookie_choice')) {
    cookieBanner.classList.add('hidden');
  }

  cookieAcceptBtn.addEventListener('click', () => {
    localStorage.setItem('gic_cookie_choice', 'accepted');
    cookieBanner.classList.add('hidden');
  });

  cookieDeclineBtn.addEventListener('click', () => {
    localStorage.setItem('gic_cookie_choice', 'declined');
    cookieBanner.classList.add('hidden');
  });

  // --- Smooth scroll navigation ---
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId && targetId !== '#') {
        const targetEl = document.querySelector(targetId);
        if (targetEl) {
          e.preventDefault();
          targetEl.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  });
});
