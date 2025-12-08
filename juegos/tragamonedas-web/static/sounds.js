// Sistema de sonidos para la tragamonedas
// Usando Web Audio API para generar tonos

class SoundManager {
  constructor() {
    this.audioContext = null;
    this.masterVolume = 0.3; // Volumen moderado
    this.init();
  }

  init() {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) {
      console.warn('Web Audio API no soportada');
    }
  }

  // Función auxiliar para crear un tono
  playTone(frequency, duration, type = 'sine', volume = 1.0) {
    if (!this.audioContext) return;

    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = type;

    gainNode.gain.setValueAtTime(this.masterVolume * volume, this.audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);

    oscillator.start(this.audioContext.currentTime);
    oscillator.stop(this.audioContext.currentTime + duration);
  }

  // Sonido de giro de rodillos (efecto mecánico)
  playSpinSound() {
    if (!this.audioContext) return;

    const now = this.audioContext.currentTime;

    // Crear ruido blanco filtrado para simular rodillos
    const bufferSize = this.audioContext.sampleRate * 0.8;
    const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
    const data = buffer.getChannelData(0);

    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }

    const noise = this.audioContext.createBufferSource();
    noise.buffer = buffer;

    const filter = this.audioContext.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.value = 800;

    const gainNode = this.audioContext.createGain();
    gainNode.gain.setValueAtTime(this.masterVolume * 0.15, now);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.8);

    noise.connect(filter);
    filter.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    noise.start(now);
    noise.stop(now + 0.8);
  }

  // Sonido de click de palanca
  playLeverSound() {
    if (!this.audioContext) return;

    const now = this.audioContext.currentTime;
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    oscillator.frequency.setValueAtTime(150, now);
    oscillator.frequency.exponentialRampToValueAtTime(50, now + 0.1);
    oscillator.type = 'square';

    gainNode.gain.setValueAtTime(this.masterVolume * 0.3, now);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.1);

    oscillator.start(now);
    oscillator.stop(now + 0.1);
  }

  // Sonido de victoria normal - VERSIÓN IMPACTANTE Y EUFÓRICA
  playWinSound() {
    if (!this.audioContext) return;

    // Fanfarria triunfal rápida y enérgica
    const fanfare = [
      { freq: 523.25, time: 0 },     // C5
      { freq: 659.25, time: 60 },    // E5
      { freq: 783.99, time: 120 },   // G5
      { freq: 1046.50, time: 180 },  // C6
      { freq: 1318.51, time: 240 }   // E6
    ];

    // Tocar fanfarria con múltiples capas
    fanfare.forEach(note => {
      setTimeout(() => {
        // Capa principal (brillante)
        this.playTone(note.freq, 0.15, 'sine', 0.5);
        // Capa de armonía (más grave)
        this.playTone(note.freq * 0.5, 0.15, 'triangle', 0.3);
        // Capa de brillo (más aguda)
        this.playTone(note.freq * 2, 0.1, 'sine', 0.2);
      }, note.time);
    });

    // Efecto de "power-up" ascendente
    setTimeout(() => {
      const now = this.audioContext.currentTime;
      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);

      oscillator.frequency.setValueAtTime(200, now);
      oscillator.frequency.exponentialRampToValueAtTime(2000, now + 0.3);
      oscillator.type = 'sawtooth';

      gainNode.gain.setValueAtTime(this.masterVolume * 0.3, now);
      gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.3);

      oscillator.start(now);
      oscillator.stop(now + 0.3);
    }, 300);

    // Acorde final explosivo
    setTimeout(() => {
      const chord = [1046.50, 1318.51, 1567.98]; // C6, E6, G6
      chord.forEach(freq => {
        this.playTone(freq, 0.4, 'sine', 0.6);
        this.playTone(freq * 0.5, 0.4, 'triangle', 0.4);
      });
    }, 350);
  }

  // Sonido de gran victoria (jackpot) - VERSIÓN ÉPICA
  playBigWinSound() {
    if (!this.audioContext) return;

    // Secuencia ascendente ultra-rápida con armonías
    const notes = [
      261.63, 329.63, 392.00, 523.25, 659.25, 783.99, 1046.50, 1318.51
    ]; // C4 a E6

    notes.forEach((freq, i) => {
      setTimeout(() => {
        // Triple capa de sonido
        this.playTone(freq, 0.15, 'sine', 0.6);
        this.playTone(freq * 0.5, 0.15, 'triangle', 0.4);
        this.playTone(freq * 1.5, 0.12, 'sine', 0.3);
      }, i * 50); // Más rápido: 50ms en lugar de 80ms
    });

    // Efecto de sirena ascendente (dramático)
    setTimeout(() => {
      const now = this.audioContext.currentTime;
      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);

      oscillator.frequency.setValueAtTime(400, now);
      oscillator.frequency.exponentialRampToValueAtTime(3000, now + 0.4);
      oscillator.type = 'sawtooth';

      gainNode.gain.setValueAtTime(this.masterVolume * 0.4, now);
      gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.4);

      oscillator.start(now);
      oscillator.stop(now + 0.4);
    }, 400);

    // Acorde final EXPLOSIVO con múltiples octavas
    setTimeout(() => {
      const finalChord = [
        523.25, 659.25, 783.99,      // Octava media
        1046.50, 1318.51, 1567.98,   // Octava alta
        261.63, 329.63               // Octava baja (profundidad)
      ];

      finalChord.forEach((freq, i) => {
        setTimeout(() => {
          this.playTone(freq, 1.0, 'sine', 0.7);
        }, i * 20);
      });

      // Efecto de "explosión" final
      setTimeout(() => {
        const now = this.audioContext.currentTime;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        oscillator.frequency.setValueAtTime(2000, now);
        oscillator.frequency.exponentialRampToValueAtTime(100, now + 0.5);
        oscillator.type = 'sawtooth';

        gainNode.gain.setValueAtTime(this.masterVolume * 0.5, now);
        gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.5);

        oscillator.start(now);
        oscillator.stop(now + 0.5);
      }, 200);
    }, 500);
  }

  // Sonido de pérdida
  playLossSound() {
    if (!this.audioContext) return;

    const notes = [392.00, 329.63, 261.63]; // G4, E4, C4 (descendente)
    notes.forEach((freq, i) => {
      setTimeout(() => {
        this.playTone(freq, 0.25, 'sine', 0.3);
      }, i * 120);
    });
  }

  // Sonido de monedas cayendo
  playCoinSound() {
    if (!this.audioContext) return;

    for (let i = 0; i < 8; i++) {
      setTimeout(() => {
        const freq = 800 + Math.random() * 400;
        this.playTone(freq, 0.05, 'sine', 0.2);
      }, i * 50);
    }
  }

  // Sonido de detención de rodillo (click suave)
  playReelStopSound() {
    if (!this.audioContext) return;

    const now = this.audioContext.currentTime;
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    oscillator.frequency.value = 200;
    oscillator.type = 'square';

    gainNode.gain.setValueAtTime(this.masterVolume * 0.15, now);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.05);

    oscillator.start(now);
    oscillator.stop(now + 0.05);
  }
}

// Crear instancia global
const soundManager = new SoundManager();
