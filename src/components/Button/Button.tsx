import React from 'react';
import './Button.css';

interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
  children: React.ReactNode;
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  onClick,
  children,
  disabled = false,
}) => {
  return (
    <button
      className={`button ${variant} ${size}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
