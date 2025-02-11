import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Avatar } from './Avatar';

test('Avatar displays "away" status with correct styling and default size dimensions', () => {
  const { container, getByAltText } = render(
    <Avatar imageUrl="test-image.png" alt="Test User" status="away" />
  );
  const img = getByAltText('Test User');
  expect(img).toHaveClass('h-12 w-12');
  const statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-yellow-500');
});
test('Avatar renders correctly without status and with "sm" size dimensions', () => {
  const { container, getByAltText } = render(
    <Avatar imageUrl="test-image.png" alt="No Status User" size="sm" />
  );
  const img = getByAltText('No Status User');
  expect(img).toHaveClass('h-8 w-8');
  expect(container.querySelector('span')).not.toBeInTheDocument();
});
test('Avatar displays "online" status with correct styling and "lg" size dimensions', () => {
  const { container, getByAltText } = render(
    <Avatar imageUrl="test-image.png" alt="Online User" size="lg" status="online" />
  );
  const img = getByAltText('Online User');
  expect(img).toHaveClass('h-16 w-16');
  const statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-green-500');
});
test('Avatar displays "offline" status with correct styling and default size dimensions', () => {
  const { container, getByAltText } = render(
    <Avatar imageUrl="test-image.png" alt="Offline User" status="offline" />
  );
  const img = getByAltText('Offline User');
  expect(img).toHaveClass('h-12 w-12');
  const statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-gray-500');
});
test('Avatar container has expected "relative inline-block" classes regardless of status or size', () => {
  const { container } = render(
    <Avatar imageUrl="test-image.png" alt="Container Test" />
  );
  const outerDiv = container.firstChild;
  expect(outerDiv).toHaveClass('relative', 'inline-block');
});
test('Avatar image always has "rounded-full" and "object-cover" classes applied', () => {
  const { getByAltText } = render(
    <Avatar imageUrl="test-image.png" alt="Styled Image" size="lg" status="online" />
  );
  const img = getByAltText('Styled Image');
  expect(img).toHaveClass('rounded-full');
  expect(img).toHaveClass('object-cover');
});
test('Avatar status indicator always includes border classes "border-2" and "border-white"', () => {
  const { container } = render(
    <Avatar imageUrl="test-image-border.png" alt="Border Test User" status="online" />
  );
  const statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('border-2');
  expect(statusIndicator).toHaveClass('border-white');
});
test('Avatar renders correct image src attribute and alt text', () => {
  const imageUrl = "sample-image.png";
  const altText = "Sample User";
  const { getByAltText } = render(
    <Avatar imageUrl={imageUrl} alt={altText} />
  );
  const img = getByAltText(altText);
  expect(img).toHaveAttribute('src', imageUrl);
  expect(img).toHaveAttribute('alt', altText);
});
test('Avatar status indicator updates correctly when status prop changes', () => {
  const { container, getByAltText, rerender } = render(
    <Avatar imageUrl="test-image.png" alt="Dynamic Status User" status="offline" />
  );
  
  let statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-gray-500');
  
  rerender(
    <Avatar imageUrl="test-image.png" alt="Dynamic Status User" status="online" />
  );
  
  statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-green-500');
});
test('Avatar removes status indicator when status prop is removed', () => {
  const { container, rerender } = render(
    <Avatar imageUrl="test-image.png" alt="Dynamic Remove Status" status="online" />
  );
  
  let statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-green-500');
  
  rerender(
    <Avatar imageUrl="test-image.png" alt="Dynamic Remove Status" />
  );
  
  statusIndicator = container.querySelector('span');
  expect(statusIndicator).not.toBeInTheDocument();
});
test('Avatar updates dimensions when size prop changes dynamically', () => {
  const { getByAltText, rerender } = render(
    <Avatar imageUrl="test-image.png" alt="Dynamic Size User" size="md" />
  );
  const img = getByAltText('Dynamic Size User');
  expect(img).toHaveClass('h-12 w-12');
  
  rerender(
    <Avatar imageUrl="test-image.png" alt="Dynamic Size User" size="lg" />
  );
  expect(img).toHaveClass('h-16 w-16');
  
  rerender(
    <Avatar imageUrl="test-image.png" alt="Dynamic Size User" size="sm" />
  );
  expect(img).toHaveClass('h-8 w-8');
});
test('Avatar updates image src attribute when imageUrl prop changes', () => {
  const { getByAltText, rerender } = render(
    <Avatar imageUrl="initial-image.png" alt="Dynamic Image Source" />
  );
  const img = getByAltText('Dynamic Image Source');
  expect(img).toHaveAttribute('src', 'initial-image.png');
  
  rerender(
    <Avatar imageUrl="updated-image.png" alt="Dynamic Image Source" />
  );
  expect(img).toHaveAttribute('src', 'updated-image.png');
});
test('Avatar matches snapshot with all props', () => {
  const { container } = render(
    <Avatar imageUrl="snapshot-test.png" alt="Snapshot Avatar" size="lg" status="away" />
  );
  expect(container.firstChild).toMatchSnapshot();
});
test('Avatar updates alt attribute when alt prop changes dynamically', () => {
  const { getByAltText, queryByAltText, rerender } = render(
    <Avatar imageUrl="test-image.png" alt="Initial Alt" />
  );
  const initialImg = getByAltText('Initial Alt');
  expect(initialImg).toBeInTheDocument();
  expect(initialImg).toHaveAttribute('alt', 'Initial Alt');
  
  rerender(
    <Avatar imageUrl="test-image.png" alt="Updated Alt" />
  );
  expect(queryByAltText('Initial Alt')).toBeNull();
  const updatedImg = getByAltText('Updated Alt');
  expect(updatedImg).toBeInTheDocument();
  expect(updatedImg).toHaveAttribute('alt', 'Updated Alt');
});
test('Avatar updates imageUrl, alt, size, and status simultaneously when props change', () => {
  const { getByAltText, container, rerender } = render(
    <Avatar imageUrl="first.png" alt="First" size="sm" status="online" />
  );
  
  const img = getByAltText('First');
  expect(img).toHaveClass('h-8 w-8');
  expect(img).toHaveAttribute('src', 'first.png');
  expect(img).toHaveAttribute('alt', 'First');
  let statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-green-500');
  
  rerender(
    <Avatar imageUrl="second.png" alt="Second" size="lg" status="offline" />
  );
  
  const updatedImg = getByAltText('Second');
  expect(updatedImg).toHaveClass('h-16 w-16');
  expect(updatedImg).toHaveAttribute('src', 'second.png');
  expect(updatedImg).toHaveAttribute('alt', 'Second');
  statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-gray-500');
});
test('Avatar renders correctly when imageUrl is an empty string', () => {
  const { container, getByAltText } = render(
    <Avatar imageUrl="" alt="Empty Image" status="online" />
  );
  const img = getByAltText('Empty Image');
  expect(img).toHaveAttribute('src', '');
  expect(img).toHaveAttribute('alt', 'Empty Image');
  expect(img).toHaveClass('h-12 w-12');
  const statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-green-500');
});
test('Avatar renders correct number of children based on status prop', () => {
  const { container: containerWithStatus } = render(
    <Avatar imageUrl="test-image.png" alt="Two Children Test" size="md" status="online" />
  );
  const outerDivWithStatus = containerWithStatus.firstChild;
  expect(outerDivWithStatus.childElementCount).toBe(2);
  expect(outerDivWithStatus.children[0].tagName).toBe('IMG');
  expect(outerDivWithStatus.children[1].tagName).toBe('SPAN');
  
  const { container: containerWithoutStatus } = render(
    <Avatar imageUrl="test-image.png" alt="One Child Test" size="md" />
  );
  const outerDivWithoutStatus = containerWithoutStatus.firstChild;
  expect(outerDivWithoutStatus.childElementCount).toBe(1);
  expect(outerDivWithoutStatus.children[0].tagName).toBe('IMG');
});
test('Avatar status indicator has correct positioning and dimensions', () => {
  const { container } = render(
    <Avatar imageUrl="test-image.png" alt="Position Test" status="online" />
  );
  const statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('absolute');
  expect(statusIndicator).toHaveClass('bottom-0');
  expect(statusIndicator).toHaveClass('right-0');
  expect(statusIndicator).toHaveClass('h-3');
  expect(statusIndicator).toHaveClass('w-3');
  expect(statusIndicator).toHaveClass('border-2');
  expect(statusIndicator).toHaveClass('border-white');
});
test('Avatar handles empty alt attribute correctly', () => {
  const { container, getByAltText } = render(
    <Avatar imageUrl="test-image.png" alt="" />
  );
  const img = getByAltText('');
  expect(img).toBeInTheDocument();
  expect(img).toHaveAttribute('alt', '');
  expect(img).toHaveClass('h-12 w-12');
  expect(container.querySelector('span')).not.toBeInTheDocument();
});
test('Avatar renders an unrecognized status prop with default styling (treating it as offline)', () => {
  const { container, getByAltText } = render(
    <Avatar imageUrl="test-image.png" alt="Invalid Status Test" status={"busy" as any} />
  );
  const img = getByAltText('Invalid Status Test');
  expect(img).toHaveClass('h-12 w-12');
  const statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-gray-500');
});
test('Avatar does not retain previous size classes when size prop changes dynamically', () => {
  const { getByAltText, rerender } = render(
    <Avatar imageUrl="test-image.png" alt="Dynamic Size Update" size="sm" />
  );
  const img = getByAltText('Dynamic Size Update');
  expect(img).toHaveClass('h-8', 'w-8');
  expect(img.className).not.toMatch(/h-12|h-16/);
  rerender(
    <Avatar imageUrl="test-image.png" alt="Dynamic Size Update" size="lg" />
  );
  expect(img).toHaveClass('h-16', 'w-16');
  expect(img.className).not.toMatch(/h-8|h-12/);
});
test('Avatar handles invalid size and invalid status props by applying undefined dimensions and offline styling', () => {
  const { container, getByAltText } = render(
    <Avatar imageUrl="invalid-props.png" alt="Invalid Props" size={"xl" as any} status={"busy" as any} />
  );
  const img = getByAltText('Invalid Props');
  expect(img.className).toContain('undefined');
  expect(img).toHaveClass('rounded-full');
  expect(img).toHaveClass('object-cover');
  const statusIndicator = container.querySelector('span');
  expect(statusIndicator).toBeInTheDocument();
  expect(statusIndicator).toHaveClass('bg-gray-500');
});
test('Avatar does not render status indicator when status is an empty string', () => {
  const { container, getByAltText } = render(
    <Avatar imageUrl="test-image.png" alt="Empty Status Test" status="" />
  );
  const img = getByAltText('Empty Status Test');
  expect(img).toHaveClass('h-12 w-12');
  expect(container.querySelector('span')).not.toBeInTheDocument();
});
/**
 * Test to ensure that Avatar renders correctly with only the required props.
 * It verifies that the default size ("md": "h-12 w-12") is applied and no status indicator is rendered.
 * A snapshot is taken to confirm that the minimal output structure matches the expected rendering.
 */
test('Avatar snapshot renders correctly with only required props', () => {
  const { container } = render(
    <Avatar imageUrl="minimal.png" alt="Minimal Avatar" />
  );
  expect(container.firstChild).toMatchSnapshot();
});
test('Avatar does not render status indicator when status is null', () => {
  /**
   * This test verifies that when the "status" prop is explicitly set to null,
   * the Avatar component behaves as if no status was provided.
   * It checks that the default dimensions for the image (size "md": "h-12 w-12") are applied
   * and confirms that the status indicator element is not rendered.
   */
  const { container, getByAltText } = render(
    <Avatar imageUrl="null-status.png" alt="Null Status Avatar" status={null as any} />
  );
  const img = getByAltText('Null Status Avatar');
  expect(img).toHaveClass('h-12 w-12');
  expect(container.querySelector('span')).not.toBeInTheDocument();
});