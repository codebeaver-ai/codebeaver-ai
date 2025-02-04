import React, { useState } from 'react';
import SearchableDropdown from './SearchableDropdown';

const countries = [
  { value: 'us', label: 'United States' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'ca', label: 'Canada' },
  { value: 'au', label: 'Australia' },
  { value: 'de', label: 'Germany' },
  { value: 'fr', label: 'France' },
  { value: 'jp', label: 'Japan' },
  { value: 'br', label: 'Brazil' },
  { value: 'in', label: 'India' },
  { value: 'cn', label: 'China' },
];

export const CountrySelector: React.FC = () => {
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  return (
    <div className="max-w-md mx-auto p-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Select a Country
      </label>
      <SearchableDropdown
        options={countries}
        value={selectedCountry}
        onChange={setSelectedCountry}
        placeholder="Choose a country..."
      />
      {selectedCountry && (
        <p className="mt-2 text-sm text-gray-600">
          Selected country code: {selectedCountry}
        </p>
      )}
    </div>
  );
};

export default CountrySelector;