import { useRef, useEffect } from 'react';
import './ParticleBackground.css';

const NODES = 60;
const CONNECT_DIST = 300;
const MAX_CONNECTIONS = 4;
const LINE_OPACITY = 0.6;
const NODE_SPEED = 0.2;

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let nodes: Node[] = [];
    let animationId: number;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      initNodes();
    };

    const initNodes = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      nodes = Array.from({ length: NODES }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * NODE_SPEED,
        vy: (Math.random() - 0.5) * NODE_SPEED,
      }));
    };

    const tick = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;

      ctx.clearRect(0, 0, w, h);

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;
        n.x = Math.max(0, Math.min(w, n.x));
        n.y = Math.max(0, Math.min(h, n.y));
      }

      ctx.strokeStyle = 'rgba(37, 99, 235, 0.39)';
      ctx.lineWidth = 1.2;

      const connectionCount = new Array(nodes.length).fill(0);
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          if (connectionCount[i] >= MAX_CONNECTIONS || connectionCount[j] >= MAX_CONNECTIONS) continue;
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.hypot(dx, dy);
          if (dist < CONNECT_DIST) {
            ctx.globalAlpha = (1 - dist / CONNECT_DIST) * LINE_OPACITY;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
            connectionCount[i] += 1;
            connectionCount[j] += 1;
          }
        }
      }
      ctx.globalAlpha = 1;

      for (let i = 0; i < nodes.length; i++) {
        ctx.fillStyle = 'rgba(37, 99, 235, 0.29)';
        ctx.beginPath();
        ctx.arc(nodes[i].x, nodes[i].y, 1.2, 0, Math.PI * 2);
        ctx.fill();
      }

      animationId = requestAnimationFrame(tick);
    };

    resize();
    window.addEventListener('resize', resize);
    tick();
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <div className="particle-background">
      <canvas ref={canvasRef} className="particle-background-canvas" />
    </div>
  );
}

export default ParticleBackground;
