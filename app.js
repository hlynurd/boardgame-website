// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.4.0/firebase-app.js";
import { getFirestore, collection, query, getDocs, writeBatch, doc, addDoc, orderBy, limit, where } from "https://www.gstatic.com/firebasejs/9.4.0/firebase-firestore.js";
const firebaseConfig = {
  apiKey: "AIzaSyBzWG9IqPoyQiubQK3krglfwjS5b36raRc",
  authDomain: "uhran-gamers.firebaseapp.com",
  databaseURL: "https://uhran-gamers-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "uhran-gamers",
  storageBucket: "uhran-gamers.appspot.com",
  messagingSenderId: "805198739137",
  appId: "1:805198739137:web:4d940d3bfef76ede818640",
  measurementId: "G-T4J9BRGWNW"
};
// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const dataDiv = document.getElementById("data");


const fetchAndDisplayGames = () => {
  getDocs(query(collection(db, "gameResults"), orderBy("order")))
      .then((querySnapshot) => {
          // Assuming dataDiv contains your table and tbody is within that table
          const tableBody = dataDiv.querySelector('tbody');
          tableBody.innerHTML = ''; // Clear existing table rows (except for the headers)
          
          querySnapshot.forEach((doc) => {
              const gameData = doc.data();
              const row = `<tr>
                  <td>${gameData.Game}</td>
                  <td>${gameData.Auðun}</td>
                  <td>${gameData.Árni}</td>
                  <td>${gameData.Hlynur}</td>
                  <td>${gameData.Kári}</td>
                  <td>${gameData.Sævar}</td>
                  <td>${gameData.Skossi}</td>
                  <td>${gameData.Örn}</td>
              </tr>`;
              tableBody.innerHTML += row; // Append new row to the table body
          });
      })
      .catch((error) => {
          console.error("Error fetching data: ", error);
          dataDiv.innerHTML = 'Failed to load data.'; // Provide feedback in case of an error
      });
};

async function deleteTestGames() {
  const gamesRef = collection(db, "gameResults");
  const batch = writeBatch(db);

  // Query for games with 'Game' field 'test'
  const queryTest = query(gamesRef, where("Game", "==", "test"));
  const querySnapshotTest = await getDocs(queryTest);
  querySnapshotTest.forEach((doc) => {
      batch.delete(doc.ref);
  });

  // Query for games with 'Game' field 'Test'
  const queryTestCap = query(gamesRef, where("Game", "==", "Test"));
  const querySnapshotTestCap = await getDocs(queryTestCap);
  querySnapshotTestCap.forEach((doc) => {
      batch.delete(doc.ref);
  });

  // Commit the batch
  await batch.commit();
  console.log("Test games deleted successfully.");
}


// document.addEventListener('DOMContentLoaded', async () => {
//   await deleteTestGames();
//   document.getElementById('addGameForm').addEventListener('submit', async (event) => {
//     event.preventDefault();
  
//     // Collecting form data
//     const gameData = {
//         Game: document.getElementById('gameName').value,
//         Auðun: document.getElementById('audunScore').value || null,
//         Árni: document.getElementById('arniScore').value || null,
//         Hlynur: document.getElementById('hlynurScore').value || null,
//         Kári: document.getElementById('kariScore').value || null,
//         Skossi: document.getElementById('skossiScore').value || null,
//         Sævar: document.getElementById('saevarScore').value || null,
//         Örn: document.getElementById('ornScore').value || null,
//         Tóta: null,
//         // Initialize 'order' with a default value, to be updated
//         order: 0
//     };
  
//     try {
//         // Fetch the highest 'order' value from the collection
//         const querySnapshot = await getDocs(query(collection(db, "gameResults"), orderBy("order", "desc"), limit(1)));
//         const lastDoc = querySnapshot.docs[0];
  
//         // If there's at least one document, set the new game's 'order' to lastDoc's order + 1
//         if (lastDoc) {
//             gameData.order = lastDoc.data().order + 1;
//         } // If there are no documents, 'order' remains 0, suitable for the first document
  
//         // Adding the new game to Firestore with the computed 'order'
//         await addDoc(collection(db, "gameResults"), gameData);
//         console.log("New game added successfully.");
  
//         // Optionally, clear the form fields
//         document.getElementById('addGameForm').reset();
  
//         // Refresh the displayed data to include the new game
//         fetchAndDisplayGames();
//     } catch (error) {
//         console.error("Error adding new game: ", error);
//     }
//   });
//   });


// Fetch data from Firestore adjusted for Firebase v9
getDocs(query(collection(db, "gameResults"), orderBy("order"))).then((querySnapshot) => {
  dataDiv.innerHTML = '<table><thead><tr><th>Game</th><th>Auðun</th><th>Árni</th><th>Hlynur</th><th>Kári</th><th>Skossi</th><th>Sævar</th><th>Örn</th></tr></thead><tbody></tbody></table>';
  const tableBody = dataDiv.querySelector('tbody');
  
  querySnapshot.forEach((doc) => {
    const gameData = doc.data();
    const row = `<tr>
        <td>${gameData.Game}</td>
        <td>${gameData.Auðun}</td>
        <td>${gameData.Árni}</td>
        <td>${gameData.Hlynur}</td>
        <td>${gameData.Kári}</td>
        <td>${gameData.Skossi}</td>
        <td>${gameData.Sævar}</td>
        <td>${gameData.Örn}</td>
    </tr>`;
    tableBody.innerHTML += row;
  });
}).catch((error) => {
  console.error("Error fetching data: ", error);
  dataDiv.innerHTML = 'Failed to load data.';
});
