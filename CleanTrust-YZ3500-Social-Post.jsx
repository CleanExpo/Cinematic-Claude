import React, { useState, useEffect } from 'react';

const CleanTrustYZ3500Poster = () => {
  const [particles, setParticles] = useState([]);
  const [scanProgress, setScanProgress] = useState(0);

  useEffect(() => {
    // Initialize scan particles
    const initialParticles = Array.from({ length: 12 }, (_, i) => ({
      id: i,
      angle: (i / 12) * Math.PI * 2,
      opacity: Math.random() * 0.6 + 0.4,
      delay: Math.random() * 0.5,
    }));
    setParticles(initialParticles);

    // Animate scan progress
    const interval = setInterval(() => {
      setScanProgress((prev) => (prev >= 100 ? 0 : prev + 2));
    }, 50);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-[1080px] h-[1080px] overflow-hidden font-sans">
      {/* Background gradient */}
      <div
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(135deg, #030810 0%, #0a1628 50%, #051220 100%)',
        }}
      />

      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `linear-gradient(0deg, transparent 24%, rgba(0, 229, 255, 0.05) 25%, rgba(0, 229, 255, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 229, 255, 0.05) 75%, rgba(0, 229, 255, 0.05) 76%, transparent 77%, transparent),
                            linear-gradient(90deg, transparent 24%, rgba(0, 229, 255, 0.05) 25%, rgba(0, 229, 255, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 229, 255, 0.05) 75%, rgba(0, 229, 255, 0.05) 76%, transparent 77%, transparent)`,
          backgroundSize: '50px 50px',
        }}
      />

      {/* Main content container */}
      <div className="relative h-full flex flex-col items-center justify-center px-12">
        {/* CCW Brand Bar */}
        <div
          className="absolute top-0 left-0 right-0 flex items-center justify-between px-8 py-4"
          style={{
            background: 'linear-gradient(180deg, rgba(3, 8, 16, 0.95), rgba(3, 8, 16, 0.6))',
            borderBottom: '1px solid rgba(0, 115, 206, 0.25)',
          }}
        >
          <div className="flex items-center gap-3">
            <div
              style={{
                width: '40px',
                height: '40px',
                border: '2px solid #0073CE',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: '"JetBrains Mono", monospace',
                fontWeight: '700',
                fontSize: '12px',
                color: '#0073CE',
                boxShadow: '0 0 15px rgba(0, 115, 206, 0.4)',
              }}
            >
              CCW
            </div>
            <div>
              <div style={{ fontFamily: '"Inter", sans-serif', fontWeight: '600', fontSize: '14px', color: '#ffffff' }}>
                Carpet Cleaners Warehouse
              </div>
              <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '9px', color: '#0073CE', letterSpacing: '2px', textTransform: 'uppercase' }}>
                ccwonline.com.au
              </div>
            </div>
          </div>
          <div
            style={{
              padding: '6px 16px',
              border: '1px solid #0073CE',
              borderRadius: '4px',
              background: 'rgba(0, 115, 206, 0.15)',
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: '10px',
              color: '#ffffff',
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
            }}
          >
            Shop Now
          </div>
        </div>

        {/* Top section: Product name and tagline */}
        <div className="absolute left-0 right-0 text-center" style={{ top: '80px' }}>
          <div
            className="text-4xl font-bold mb-3"
            style={{
              color: '#ffffff',
              fontFamily: '"Inter", sans-serif',
              letterSpacing: '1px',
            }}
          >
            CleanTrust Touch™
          </div>
          <div
            className="text-2xl font-light"
            style={{
              color: '#00e5ff',
              fontFamily: '"Inter", sans-serif',
              letterSpacing: '0.5px',
            }}
          >
            YZ3500 Luminometer
          </div>
        </div>

        {/* Center: Device visualization and RLU display */}
        <div className="relative w-96 h-96 flex items-center justify-center mb-12">
          {/* Outer glow container */}
          <div
            className="absolute inset-0 rounded-full opacity-40"
            style={{
              background: 'radial-gradient(circle, rgba(0, 229, 255, 0.3) 0%, transparent 70%)',
              filter: 'blur(40px)',
            }}
          />

          {/* Device body schematic */}
          <svg className="absolute w-56 h-56 -top-8" viewBox="0 0 200 240">
            {/* Main device body */}
            <rect
              x="50"
              y="40"
              width="100"
              height="140"
              fill="none"
              stroke="#00e5ff"
              strokeWidth="2"
              rx="8"
            />

            {/* Top display area */}
            <rect
              x="65"
              y="55"
              width="70"
              height="50"
              fill="none"
              stroke="#00e5ff"
              strokeWidth="1.5"
              rx="3"
              opacity="0.7"
            />

            {/* Display lines */}
            <line x1="75" y1="65" x2="125" y2="65" stroke="#00e5ff" strokeWidth="1" opacity="0.5" />
            <line x1="75" y1="75" x2="125" y2="75" stroke="#00e5ff" strokeWidth="1" opacity="0.5" />
            <line x1="75" y1="85" x2="110" y2="85" stroke="#00e5ff" strokeWidth="1" opacity="0.5" />

            {/* Sample insertion slot */}
            <rect
              x="85"
              y="120"
              width="30"
              height="35"
              fill="none"
              stroke="#00e5ff"
              strokeWidth="1.5"
              opacity="0.8"
            />

            {/* Bottom section */}
            <rect
              x="65"
              y="162"
              width="70"
              height="12"
              fill="none"
              stroke="#00e5ff"
              strokeWidth="1"
              opacity="0.6"
            />

            {/* Power indicator */}
            <circle cx="75" cy="175" r="3" fill="#00e5ff" opacity="0.8" />
          </svg>

          {/* RLU display rings */}
          <div className="relative w-80 h-80 flex items-center justify-center">
            {/* Outer ring */}
            <div
              className="absolute rounded-full"
              style={{
                width: '320px',
                height: '320px',
                border: '2px solid rgba(0, 229, 255, 0.2)',
                animation: 'pulse 3s ease-in-out infinite',
              }}
            />

            {/* Middle ring */}
            <div
              className="absolute rounded-full"
              style={{
                width: '240px',
                height: '240px',
                border: '1.5px solid rgba(0, 229, 255, 0.35)',
              }}
            />

            {/* Inner ring */}
            <div
              className="absolute rounded-full"
              style={{
                width: '160px',
                height: '160px',
                border: '1.5px solid rgba(0, 229, 255, 0.5)',
              }}
            />

            {/* Central glow sphere */}
            <div
              className="absolute rounded-full flex items-center justify-center"
              style={{
                width: '140px',
                height: '140px',
                background: 'radial-gradient(circle at 35% 35%, rgba(0, 229, 255, 0.6), rgba(5, 18, 32, 0.9))',
                border: '2px solid #00e5ff',
                boxShadow: '0 0 40px rgba(0, 229, 255, 0.8), inset 0 0 40px rgba(0, 229, 255, 0.3)',
              }}
            >
              {/* RLU reading */}
              <div className="text-center">
                <div
                  style={{
                    fontSize: '48px',
                    fontWeight: '700',
                    color: '#00e5ff',
                    fontFamily: '"JetBrains Mono", monospace',
                    letterSpacing: '2px',
                    textShadow: '0 0 20px rgba(0, 229, 255, 0.8)',
                  }}
                >
                  142
                </div>
                <div
                  style={{
                    fontSize: '13px',
                    color: 'rgba(0, 229, 255, 0.7)',
                    fontFamily: '"JetBrains Mono", monospace',
                    marginTop: '4px',
                    letterSpacing: '1px',
                  }}
                >
                  RLU
                </div>
              </div>
            </div>

            {/* Scan particles */}
            {particles.map((particle) => {
              const x = Math.cos(particle.angle) * 140;
              const y = Math.sin(particle.angle) * 140;
              const distance = 100 + scanProgress;
              const px = Math.cos(particle.angle) * distance;
              const py = Math.sin(particle.angle) * distance;

              return (
                <div
                  key={particle.id}
                  className="absolute w-1 h-1 rounded-full"
                  style={{
                    background: '#00e5ff',
                    left: '50%',
                    top: '50%',
                    transform: `translate(calc(-50% + ${px}px), calc(-50% + ${py}px))`,
                    opacity: Math.max(0, 1 - scanProgress / 100) * particle.opacity,
                    boxShadow: '0 0 8px rgba(0, 229, 255, 0.8)',
                    transition: 'all 0.05s linear',
                  }}
                />
              );
            })}
          </div>
        </div>

        {/* 4-Step process */}
        <div className="relative mt-8 flex gap-8 justify-center">
          {['Swab', 'Insert', 'Analyse', 'Result'].map((step, index) => (
            <div key={index} className="flex flex-col items-center gap-3">
              {/* Step number circle */}
              <div
                className="relative w-12 h-12 rounded-full flex items-center justify-center"
                style={{
                  background: index <= 2 ? 'rgba(0, 229, 255, 0.2)' : 'rgba(0, 229, 255, 0.1)',
                  border: '1.5px solid #00e5ff',
                  boxShadow: index <= 2 ? '0 0 12px rgba(0, 229, 255, 0.5)' : 'none',
                }}
              >
                <span
                  style={{
                    color: '#00e5ff',
                    fontFamily: '"JetBrains Mono", monospace',
                    fontSize: '14px',
                    fontWeight: '600',
                  }}
                >
                  {index + 1}
                </span>
              </div>

              {/* Step label */}
              <div
                style={{
                  color: '#ffffff',
                  fontFamily: '"Inter", sans-serif',
                  fontSize: '12px',
                  fontWeight: '500',
                  letterSpacing: '0.5px',
                }}
              >
                {step}
              </div>

              {/* Connector line (except last) */}
              {index < 3 && (
                <div
                  className="absolute h-px w-6"
                  style={{
                    background: 'linear-gradient(90deg, #00e5ff, transparent)',
                    left: `calc(50% + 32px + ${index * 104}px)`,
                    top: '60px',
                    opacity: 0.5,
                  }}
                />
              )}
            </div>
          ))}
        </div>

        {/* Bottom section: CTA + CCW Branding */}
        <div className="absolute bottom-0 left-0 right-0 text-center" style={{ paddingBottom: '20px' }}>
          <div
            className="text-lg font-light mb-4"
            style={{
              color: '#00e5ff',
              fontFamily: '"Inter", sans-serif',
              letterSpacing: '0.5px',
            }}
          >
            See the invisible. Prove the clean.
          </div>

          {/* Buy Now Button */}
          <div
            style={{
              display: 'inline-block',
              padding: '10px 32px',
              background: '#0073CE',
              borderRadius: '4px',
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: '13px',
              fontWeight: '700',
              color: '#ffffff',
              letterSpacing: '2px',
              textTransform: 'uppercase',
              boxShadow: '0 0 30px rgba(0, 115, 206, 0.4), 0 4px 20px rgba(0, 0, 0, 0.3)',
              marginBottom: '12px',
            }}
          >
            Buy Now — $5,291.49 AUD
          </div>

          {/* CCW Footer */}
          <div className="flex items-center justify-center gap-2" style={{ marginTop: '8px' }}>
            <div
              style={{
                width: '20px',
                height: '20px',
                border: '1.5px solid #0073CE',
                borderRadius: '3px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: '"JetBrains Mono", monospace',
                fontWeight: '700',
                fontSize: '6px',
                color: '#0073CE',
              }}
            >
              CCW
            </div>
            <div style={{ fontFamily: '"Inter", sans-serif', fontSize: '11px', color: 'rgba(232, 237, 245, 0.5)' }}>
              Carpet Cleaners Warehouse
            </div>
            <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '10px', color: '#0073CE', letterSpacing: '1px' }}>
              ccwonline.com.au
            </div>
          </div>
        </div>
      </div>

      {/* CSS animations */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

        @keyframes pulse {
          0%, 100% {
            opacity: 0.2;
          }
          50% {
            opacity: 0.4;
          }
        }

        @keyframes glow {
          0%, 100% {
            box-shadow: 0 0 20px rgba(0, 229, 255, 0.6);
          }
          50% {
            box-shadow: 0 0 40px rgba(0, 229, 255, 0.9);
          }
        }
      `}</style>
    </div>
  );
};

export default CleanTrustYZ3500Poster;
