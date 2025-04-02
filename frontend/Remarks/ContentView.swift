import SwiftUI

struct ContentView: View {
    @State private var message: String = "Loading..."
    
    var body: some View {
        VStack {
            Text("Remarks")
                .font(.largeTitle)
                .padding()
            
            Text(message)
                .padding()
            
            Button("Check API") {
                checkAPI()
            }
            .padding()
        }
        .onAppear {
            checkAPI()
        }
    }
    
    private func checkAPI() {
        guard let url = URL(string: "http://localhost:8000/health") else { return }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            if let data = data {
                if let decodedResponse = try? JSONDecoder().decode(HealthResponse.self, from: data) {
                    DispatchQueue.main.async {
                        self.message = "API Status: \(decodedResponse.status)"
                    }
                }
            }
        }.resume()
    }
}

struct HealthResponse: Codable {
    let status: String
}

#Preview {
    ContentView()
} 