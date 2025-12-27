import { useState } from "react";
import { IconButton, Paper } from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import SendIcon from '@mui/icons-material/Send';
import Button from '@mui/material/Button';
import BasicTable from "./components/Table.jsx";
import "./App.css";
import logo from "./assets/my_logo.png";

function App() {
  const [file, setFile] = useState(null);
  const [rows, setRows] = useState([]);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const formData = new FormData();
  if (file) {
    formData.append("file", file);
  }

  const handleFindMatch = async () => {
    const response = await fetch("http://localhost:8000/find-match", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    setRows(result.matches);
    console.log(result);
  }



  return (
    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 20, alignItems: "center" }}>
      <img src={logo} alt="my_logo" className="app-logo" />
      <input
        accept="*"
        type="file"
        style={{ display: "none" }}
        id="file-upload-input"
        onChange={handleFileChange}
      />

      <label htmlFor="file-upload-input">
        <Paper
          elevation={3}
          sx={{
            display: "inline-block",
            p: 5,
            borderRadius: 2,
            backgroundColor: "#E8D1C5" /* slight translucent panel */,
          }}
        >
          <IconButton component="span" aria-label="upload file">
            <UploadFileIcon
              style={{
                fontSize: 120,
                color: "#57595B",
              }}
            />
          </IconButton>
          <p style={{ 
            textAlign: "center", 
            marginTop: 5,
            marginBottom: 0,  
          }}>Upload a CV</p>
        </Paper>
      </label>

      {file && <p>Selected file: {file.name}</p>}

      <Button 
        variant="contained" 
        endIcon={<SendIcon />} 
        disabled={!file}
        sx={{ 
          backgroundColor: "#E8D1C5", 
          color: "#57595B",
        }}
        onClick={handleFindMatch}
      >
        Find Match
      </Button>

      <BasicTable rows={rows} />
    </div>
  );
}

export default App;
