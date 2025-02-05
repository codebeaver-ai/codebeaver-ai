import { capitalizeWords } from '../stringOperations';

describe('stringOperations', () => {
  it('capitalizeWords: should capitalize first letter of each word', () => {
    expect(capitalizeWords('hello world')).toBe('Hello World');
  });
});