import React, { useState } from 'react';
import './Dropdown.css';

interface Option {
  value: string;
  label: string;
}

interface DropdownProps {
  options: Option[];
  placeholder?: string;
  onChange: (value: string) => void;
  value?: string;
}

export const Dropdown: React.FC<DropdownProps> = ({
  options,
  placeholder = 'Select an option',
  onChange,
  value,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (option: Option) => {
    onChange(option.value);
    setIsOpen(false);
  };

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <div className="dropdown-container">
      <div 
        className="dropdown-header" 
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>{selectedOption?.label || placeholder}</span>
        <span className={`arrow ${isOpen ? 'up' : 'down'}`}>▼</span>
      </div>
      {isOpen && (
        <ul className="dropdown-list">
          {options.map((option) => (
            <li
              key={option.value}
              onClick={() => handleSelect(option)}
              className={option.value === value ? 'selected' : ''}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
