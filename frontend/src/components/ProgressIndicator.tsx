import './ProgressIndicator.css';

interface ProgressIndicatorProps {
  currentState: string;
  isComplete: boolean;
}

const FLOW_STEPS = [
  { key: 'zip_code', label: 'Location' },
  { key: 'full_name', label: 'Name' },
  { key: 'email', label: 'Email' },
  { key: 'vehicle', label: 'Vehicle' },
  { key: 'license', label: 'License' },
];

function getStepIndex(state: string): number {
  if (state.includes('zip')) return 0;
  if (state.includes('name')) return 1;
  if (state.includes('email')) return 2;
  // Check license first before vehicle (to avoid matching "add_another_vehicle")
  if (state.includes('license') || state === 'complete') return 4;
  // Vehicle-related states including all vehicle info collection
  if (state.includes('vehicle') || state.includes('commute') || state.includes('mileage') || state.includes('blind') || state.includes('vin') || state.includes('make') || state.includes('body') || state.includes('use')) return 3;
  return 0;
}

export function ProgressIndicator({ currentState, isComplete }: ProgressIndicatorProps) {
  const currentIndex = isComplete ? FLOW_STEPS.length : getStepIndex(currentState);
  
  return (
    <div className="progress-container">
      <div className="progress-steps">
        {FLOW_STEPS.map((step, index) => (
          <div key={step.key} className="step-wrapper">
            <div 
              className={`step ${
                index < currentIndex ? 'completed' : 
                index === currentIndex ? 'active' : 'pending'
              }`}
            >
              {index < currentIndex ? (
                <svg viewBox="0 0 24 24" fill="currentColor" className="check-icon">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
              ) : (
                <span className="step-number">{index + 1}</span>
              )}
            </div>
            <span className={`step-label ${index <= currentIndex ? 'active' : ''}`}>
              {step.label}
            </span>
            {index < FLOW_STEPS.length - 1 && (
              <div className={`step-connector ${index < currentIndex ? 'completed' : ''}`} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

