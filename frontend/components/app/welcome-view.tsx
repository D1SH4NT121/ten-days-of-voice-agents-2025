import { useState } from 'react';
import { Button } from '@/components/livekit/button';

function WelcomeImage() {
  return (
    <svg
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-fg0 mb-4 size-16"
    >
      <path
        d="M32 8L36 20H48L38 28L42 40L32 32L22 40L26 28L16 20H28L32 8Z"
        fill="currentColor"
      />
    </svg>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: (playerName?: string) => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [playerName, setPlayerName] = useState('');

  const handleStartCall = () => {
    onStartCall(playerName.trim() || undefined);
  };

  return (
    <div ref={ref}>
      <section className="bg-background flex flex-col items-center justify-center text-center">
        <WelcomeImage />

        <h1 className="text-foreground text-3xl font-bold mb-2">
          Improv Battle
        </h1>
        
        <p className="text-foreground max-w-prose pt-1 leading-6 font-medium mb-6">
          Ready to test your improv skills? Enter your name and let's battle!
        </p>

        <div className="mb-6">
          <input
            type="text"
            placeholder="Enter your name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-center text-lg mb-4 w-64"
            onKeyPress={(e) => e.key === 'Enter' && handleStartCall()}
          />
        </div>

        <Button variant="primary" size="lg" onClick={handleStartCall} className="mt-2 w-64 font-mono">
          Start Improv Battle
        </Button>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center">
        <p className="text-muted-foreground max-w-prose pt-1 text-xs leading-5 font-normal text-pretty md:text-sm">
          Get ready for an interactive improv experience with AI!
        </p>
      </div>
    </div>
  );
};
