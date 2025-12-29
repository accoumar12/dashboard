import { useEffect, useRef, useState } from "react";

export const AnimatedDogLogo = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rotation, setRotation] = useState({ x: 0, y: 0 });
  const [eyePosition, setEyePosition] = useState({
    left: { x: 88, y: 100 },
    right: { x: 112, y: 100 },
  });
  const [blink, setBlink] = useState(false);
  const [headNod, setHeadNod] = useState(0);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent | TouchEvent) => {
      if (!containerRef.current) return;

      const bounds = containerRef.current.getBoundingClientRect();
      const containerCenterX = bounds.left + bounds.width / 2;
      const containerCenterY = bounds.top + bounds.height / 2;

      let clientX: number, clientY: number;
      if ("touches" in event) {
        clientX = event.touches[0]?.clientX ?? 0;
        clientY = event.touches[0]?.clientY ?? 0;
      } else {
        clientX = event.clientX;
        clientY = event.clientY;
      }

      if (
        clientX <= 0 ||
        clientY <= 0 ||
        clientX >= window.innerWidth ||
        clientY >= window.innerHeight
      ) {
        setRotation({ x: 0, y: 0 });
        setEyePosition({
          left: { x: 88, y: 100 },
          right: { x: 112, y: 100 },
        });
        return;
      }

      const deltaX = clientX - containerCenterX;
      const deltaY = clientY - containerCenterY;

      const rotationX = (deltaY / bounds.height) * 5;
      const rotationY = (deltaX / bounds.width) * 5;

      setRotation({
        x: Math.max(-25, Math.min(25, rotationX)),
        y: Math.max(-25, Math.min(25, rotationY)),
      });

      const eyeMovementScale = 0.2;
      const eyeX = (deltaX / bounds.width) * eyeMovementScale;
      const eyeY = (deltaY / bounds.height) * eyeMovementScale;

      setEyePosition({
        left: { x: 88 + eyeX, y: 100 + eyeY },
        right: { x: 112 + eyeX, y: 100 + eyeY },
      });
    };

    const resetPosition = () => {
      setRotation({ x: 0, y: 0 });
      setEyePosition({
        left: { x: 88, y: 100 },
        right: { x: 112, y: 100 },
      });
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("touchmove", handleMouseMove, { passive: true });
    window.addEventListener("touchstart", handleMouseMove, { passive: true });
    window.addEventListener("mouseleave", resetPosition);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("touchmove", handleMouseMove);
      window.removeEventListener("touchstart", handleMouseMove);
      window.removeEventListener("mouseleave", resetPosition);
    };
  }, []);

  useEffect(() => {
    const blinkInterval = setInterval(
      () => {
        setBlink(true);
        setTimeout(() => setBlink(false), 300);
      },
      Math.random() * 5000 + 3000
    );

    const nodInterval = setInterval(
      () => {
        const randomNod =
          Math.random() > 0.5 ? Math.random() * 3 : -Math.random() * 3;
        setHeadNod(randomNod);
        setTimeout(() => setHeadNod(0), 500);
      },
      Math.random() * 5000 + 3000
    );

    return () => {
      clearInterval(blinkInterval);
      clearInterval(nodInterval);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: '84px',
        height: '84px',
        cursor: 'pointer',
        overflow: 'visible',
        transition: 'transform 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
      }}
    >
      <svg
        viewBox="0 0 200 200"
        width="100%"
        height="100%"
        style={{
          transform: `perspective(1000px) rotateX(${rotation.x}deg) rotateY(${rotation.y}deg) rotateX(${headNod}deg)`,
          transition: "transform 0.1s ease-out",
        }}
      >
        {/* Head */}
        <circle cx="100" cy="105" r="55" fill="#f2c48d" />

        {/* Ears */}
        <ellipse cx="50" cy="95" rx="18" ry="32" fill="#d19a66" />
        <ellipse cx="150" cy="95" rx="18" ry="32" fill="#d19a66" />

        {/* Eyes */}
        <ellipse
          cx={eyePosition.left.x}
          cy={eyePosition.left.y}
          rx={3.5}
          ry={blink ? 1 : 4.5}
          fill="#000"
          style={{ transition: "ry 0.15s ease-in-out" }}
        />
        <ellipse
          cx={eyePosition.right.x}
          cy={eyePosition.right.y}
          rx={3.5}
          ry={blink ? 1 : 4.5}
          fill="#000"
          style={{ transition: "ry 0.15s ease-in-out" }}
        />

        {/* Nose */}
        <ellipse cx="100" cy="118" rx="8" ry="6" fill="#3b2f2f" />

        {/* Mouth */}
        <path
          d="M92 130 Q100 136 108 130"
          stroke="#3b2f2f"
          strokeWidth="2"
          fill="none"
        />

        {/* Tongue */}
        <path
          d="M96 130 Q100 138 104 130 V135 Q100 140 96 135 Z"
          fill="#f48fb1"
        />
      </svg>
    </div>
  );
};
