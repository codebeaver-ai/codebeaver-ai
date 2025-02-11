import React, { useState } from 'react';
import { Button } from './components/Button/Button';
import { Dropdown } from './components/Dropdown/Dropdown';
import './App.css';

const App: React.FC = () => {
  const [selectedOption, setSelectedOption] = useState<string>('');
  
  const dropdownOptions = [
    { value: 'react', label: 'React' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'jest', label: 'Jest' },
  ];

  const handleButtonClick = () => {
    alert(`You selected: ${selectedOption || 'nothing yet'}`);
  };

  return (
    <div className="app">
      <h1>TypeScript React Demo</h1>
      
      <section className="component-section">
        <h2>Button Component</h2>
        <div className="button-container">
          <Button onClick={() => alert('Primary clicked!')}>
            Primary Button
          </Button>
          <Button variant="secondary" onClick={() => alert('Secondary clicked!')}>
            Secondary Button
          </Button>
          <Button disabled>
            Disabled Button
          </Button>
        </div>
      </section>

      <section className="component-section">
        <h2>Dropdown Component</h2>
        <div className="dropdown-container">
          <Dropdown
            options={dropdownOptions}
            value={selectedOption}
            onChange={setSelectedOption}
            placeholder="Select a technology"
          />
          <Button 
            onClick={handleButtonClick}
            variant="primary"
            size="small"
          >
            Check Selection
          </Button>
        </div>
      </section>
    </div>
  );
};

export default App;
