// src/components/Avatar/Avatar.tsx
import React from 'react';

interface AvatarProps {
  imageUrl: string;
  alt: string;
  size?: 'sm' | 'md' | 'lg';
  status?: 'online' | 'offline' | 'away';
}

export const Avatar: React.FC<AvatarProps> = ({
  imageUrl,
  alt,
  size = 'md',
  status
}) => {
  const dimensions = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16'
  }[size];

  return (
    <div className="relative inline-block">
      <img 
        src={imageUrl}
        alt={alt}
        className={`${dimensions} rounded-full object-cover`}
      />
      {status && (
        <span 
          className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white
            ${status === 'online' ? 'bg-green-500' : 
              status === 'away' ? 'bg-yellow-500' : 'bg-gray-500'
            }`}
        />
      )}
    </div>
  );
};