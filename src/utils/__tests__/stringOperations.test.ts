import { capitalizeWords, reverseWords } from '../stringOperations';

describe('stringOperations', () => {
  it('capitalizeWords: should capitalize first letter of each word', () => {
    expect(capitalizeWords('hello world')).toBe('Hello World');
  });

  it('reverseWords: should reverse the order of words in a string', () => {
    /**
     * This test verifies that the reverseWords function correctly
     * reverses the order of words in the input string while
     * maintaining the original capitalization and spacing.
     */
    expect(reverseWords('Hello World from TypeScript')).toBe('TypeScript from World Hello');
  });
});
