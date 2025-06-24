import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AIAssistantArtist from '../../digital-ai-mentor/src/components/AIAssistantArtist';
import AIAssistantStudent from '../../digital-ai-mentor/src/components/AIAssistantStudent';
import AIAssistantBusiness from '../../digital-ai-mentor/src/components/AIAssistantBusiness';
import AIAssistantDeveloper from '../../digital-ai-mentor/src/components/AIAssistantDeveloper';
import AIAssistantExecutive from '../../digital-ai-mentor/src/components/AIAssistantExecutive';
import AIAssistantAnalyst from '../../digital-ai-mentor/src/components/AIAssistantAnalyst';
import AIAssistant from '../../digital-ai-mentor/src/components/AIAssistant';

const personas = [
  { key: 'student', name: 'Student', icon: '🎓' },
  { key: 'artist', name: 'Artist', icon: '🎨' },
  { key: 'business', name: 'Business', icon: '💼' },
  { key: 'developer', name: 'Developer', icon: '💻' },
  { key: 'executive', name: 'Executive', icon: '📈' },
  { key: 'analyst', name: 'Analyst', icon: '🧮' },
];

const DraChatPage = () => {
  const { persona } = useParams();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);
  const currentPersona = personas.find(p => p.key === persona) || personas[0];

  const handlePersonaChange = (key: string) => {
    setShowDropdown(false);
    navigate(`/dra-chat/${key}`);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 border-b bg-white shadow-sm relative">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{currentPersona.icon}</span>
          <span className="font-bold text-lg">{currentPersona.name} Assistant</span>
        </div>
        <div className="relative">
          <button
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg shadow hover:bg-gray-200 transition"
            onClick={() => setShowDropdown(v => !v)}
          >
            <span>{currentPersona.icon}</span>
            <span className="font-medium">{currentPersona.name}</span>
            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
          </button>
          {showDropdown && (
            <div className="absolute right-0 mt-2 w-48 bg-white border rounded-lg shadow-lg z-10">
              {personas.map(p => (
                <button
                  key={p.key}
                  className={`w-full flex items-center gap-2 px-4 py-2 hover:bg-gray-100 transition text-left ${p.key === currentPersona.key ? 'bg-gray-100 font-semibold' : ''}`}
                  onClick={() => handlePersonaChange(p.key)}
                >
                  <span className="text-xl">{p.icon}</span>
                  <span>{p.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </header>
      <main className="flex-1">
        {/* Render the correct assistant based on persona */}
        {(() => {
          switch (persona) {
            case 'artist':
              return <AIAssistantArtist />;
            case 'student':
              return <AIAssistantStudent />;
            case 'business':
              return <AIAssistantBusiness />;
            case 'developer':
              return <AIAssistantDeveloper />;
            case 'executive':
              return <AIAssistantExecutive />;
            case 'analyst':
              return <AIAssistantAnalyst />;
            default:
              return <AIAssistant />;
          }
        })()}
      </main>
    </div>
  );
};

export default DraChatPage; 