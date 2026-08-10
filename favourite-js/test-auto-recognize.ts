// Test script for auto-recognition functionality
import { autoRecognizeItem } from './src/utils/autoRecognize'

async function testAutoRecognize() {
  console.log('Testing auto-recognition functionality...\n')

  // Test URL recognition
  console.log('1. Testing URL recognition:')
  const urlTestCases = [
    'https://github.com/microsoft/TypeScript',
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'https://stackoverflow.com/questions/12345678',
    'https://www.w3schools.com/html/',
    'https://example.com'
  ]

  for (const url of urlTestCases) {
    try {
      const result = await autoRecognizeItem(url, 'link')
      console.log(`  URL: ${url}`)
      console.log(`    Title: ${result.title}`)
      console.log(`    Category: ${result.category}`)
      console.log(`    Summary: ${result.summary || '(none)'}\n`)
    } catch (error) {
      console.log(`  Error processing ${url}: ${error}\n`)
    }
  }

  // Test file recognition
  console.log('2. Testing file recognition:')
  const fileTestCases = [
    'C:\\Users\\Documents\\report.pdf',
    '/home/user/pictures/photo.jpg',
    'document.tex',
    'script.js',
    'data.csv',
    'archive.zip'
  ]

  for (const file of fileTestCases) {
    try {
      const result = await autoRecognizeItem(file, 'file')
      console.log(`  File: ${file}`)
      console.log(`    Title: ${result.title}`)
      console.log(`    Category: ${result.category}`)
      console.log(`    Summary: ${result.summary || '(none)'}\n`)
    } catch (error) {
      console.log(`  Error processing ${file}: ${error}\n`)
    }
  }

  console.log('Auto-recognition test completed.')
}

// Run the test if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testAutoRecognize().catch(console.error)
}