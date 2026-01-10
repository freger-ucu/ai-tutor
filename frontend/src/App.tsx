function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-indigo-900 mb-4">
            AI Tutor
          </h1>
          <p className="text-2xl text-indigo-600 mb-8">
            Personalized Learning Platform
          </p>
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-md mx-auto">
            <p className="text-gray-600">
              Welcome to AI Tutor. This platform will help students learn through
              personalized exercises and intelligent feedback.
            </p>
            <div className="mt-6 space-y-2 text-sm text-gray-500">
              <p>Backend: <code className="bg-gray-100 px-2 py-1 rounded">localhost:8000</code></p>
              <p>Frontend: <code className="bg-gray-100 px-2 py-1 rounded">localhost:5173</code></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
