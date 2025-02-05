export function capitalizeWords(input: string): string {
  /**
 * Capitalizes the first letter of each word in the input string.
 * @param input - The string to be processed
 * @returns The input string with each word capitalized
 */
  if (!input) return '';
  return input
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}


export function reverseWords(input: string): string {
  /**
   * Reverses the order of words in the input string.
   * @param input - The string to be processed
   * @returns The input string with words in reverse order
   */
  if (!input) return '';
  return input.split(' ').reverse().join(' ');
}