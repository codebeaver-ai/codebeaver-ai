import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders children correctly', () => {
    const { getByText } = render(<Button>Click me</Button>);
    expect(getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    const { getByText } = render(
      <Button onClick={handleClick}>Click me</Button>
    );
    
    fireEvent.click(getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies variant classes correctly', () => {
    const { container } = render(
      <Button variant="secondary">Click me</Button>
    );
    
    expect(container.firstChild).toHaveClass('secondary');
  });

  it('is disabled when disabled prop is true', () => {
    const { container } = render(
      <Button disabled>Click me</Button>
    );
    
    expect(container.firstChild).toBeDisabled();
  });
});
