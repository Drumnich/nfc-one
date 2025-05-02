import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import {
  AppBar, Toolbar, Typography, Button, Box, Container, Paper, Tabs, Tab, TextField, Card, CardContent, List, ListItem, ListItemText, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, Snackbar, Alert, MenuItem, Select, InputLabel, FormControl
} from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

function Auth({ onAuth }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState('login');
  const [error, setError] = useState('');

  const handleAuth = async (e) => {
    e.preventDefault();
    setError('');
    if (mode === 'login') {
      const { error, data } = await supabase.auth.signInWithPassword({ email, password });
      if (error) setError(error.message);
      else onAuth(data.user);
    } else {
      const { error, data } = await supabase.auth.signUp({ email, password });
      if (error) setError(error.message);
      else onAuth(data.user);
    }
  };

  return (
    <Container maxWidth="xs" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h5" align="center" gutterBottom>
          {mode === 'login' ? 'Login' : 'Sign Up'}
        </Typography>
        <form onSubmit={handleAuth}>
          <TextField label="Email" fullWidth margin="normal" value={email} onChange={e => setEmail(e.target.value)} />
          <TextField label="Password" type="password" fullWidth margin="normal" value={password} onChange={e => setPassword(e.target.value)} />
          {error && <Typography color="error">{error}</Typography>}
          <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }}>
            {mode === 'login' ? 'Login' : 'Sign Up'}
          </Button>
        </form>
        <Button onClick={() => setMode(mode === 'login' ? 'signup' : 'login')} sx={{ mt: 2 }} fullWidth>
          {mode === 'login' ? 'Need an account? Sign Up' : 'Already have an account? Login'}
        </Button>
      </Paper>
    </Container>
  );
}

function Dashboard({ user, onLogout }) {
  const [tab, setTab] = useState(0);
  const [cards, setCards] = useState([]);
  const [locations, setLocations] = useState([]);
  const [cardHistory, setCardHistory] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [renameDialog, setRenameDialog] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [newLocationDesc, setNewLocationDesc] = useState('');
  const [assignDialog, setAssignDialog] = useState(false);
  const [assignLocation, setAssignLocation] = useState('');
  const [scanResult, setScanResult] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Fetch cards, locations, and history
  useEffect(() => {
    fetchCards();
    fetchLocations();
    fetchCardHistory();
  }, []);

  const fetchCards = async () => {
    const { data } = await supabase.from('cards').select('*').eq('user_id', user.id);
    setCards(data || []);
  };
  const fetchLocations = async () => {
    const { data } = await supabase.from('locations').select('*').eq('user_id', user.id);
    setLocations(data || []);
  };
  const fetchCardHistory = async () => {
    const { data } = await supabase.from('card_history').select('*').eq('user_id', user.id).order('last_seen', { ascending: false });
    setCardHistory(data || []);
  };

  // Card actions
  const handleRenameCard = async () => {
    if (!selectedCard) return;
    await supabase.from('cards').update({ name: renameValue }).eq('id', selectedCard.id);
    setRenameDialog(false);
    setRenameValue('');
    fetchCards();
    setSnackbar({ open: true, message: 'Card renamed!', severity: 'success' });
  };
  const handleDeleteCard = async (card) => {
    await supabase.from('cards').delete().eq('id', card.id);
    fetchCards();
    setSnackbar({ open: true, message: 'Card deleted!', severity: 'info' });
  };

  // Location actions
  const handleAddLocation = async () => {
    if (!newLocation) return;
    await supabase.from('locations').insert({ user_id: user.id, name: newLocation, description: newLocationDesc });
    setNewLocation('');
    setNewLocationDesc('');
    fetchLocations();
    setSnackbar({ open: true, message: 'Location added!', severity: 'success' });
  };
  const handleDeleteLocation = async (loc) => {
    await supabase.from('locations').delete().eq('id', loc.id);
    fetchLocations();
    setSnackbar({ open: true, message: 'Location deleted!', severity: 'info' });
  };

  // Assign card to location
  const handleAssignCard = async () => {
    if (!selectedCard || !assignLocation) return;
    await supabase.from('access_points').insert({ user_id: user.id, location_id: assignLocation, card_id: selectedCard.id });
    setAssignDialog(false);
    setAssignLocation('');
    setSnackbar({ open: true, message: 'Card assigned to location!', severity: 'success' });
  };

  // NFC scan
  const handleNFCScan = async () => {
    try {
      const response = await fetch('http://localhost:5000/read_card');
      const data = await response.json();
      if (data.error) {
        setScanResult(data.error);
      } else if (data.uid) {
        setScanResult(`Card UID: ${data.uid}`);
        // Add card if not already present
        const { data: existing } = await supabase.from('cards').select('*').eq('user_id', user.id).eq('uid', data.uid);
        if (!existing || existing.length === 0) {
          await supabase.from('cards').insert({ user_id: user.id, uid: data.uid, name: 'New Card' });
          fetchCards();
          setSnackbar({ open: true, message: 'Card added!', severity: 'success' });
        } else {
          setSnackbar({ open: true, message: 'Card already exists.', severity: 'info' });
        }
      }
    } catch (err) {
      setScanResult('Error connecting to NFC reader. Is the bridge running?');
    }
  };

  return (
    <Box>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>ONE</Typography>
          <Typography sx={{ mr: 2 }}>{user.email}</Typography>
          <Button color="inherit" startIcon={<LogoutIcon />} onClick={onLogout}>Logout</Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Card Status</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Reader Status: <span style={{ color: '#2e7d32' }}>USB NFC Reader Connected</span>
          </Typography>
          <Button variant="contained" onClick={handleNFCScan} sx={{ mb: 2 }}>Scan NFC Card</Button>
          <Typography>{scanResult}</Typography>
        </Paper>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
          <Tab label="Cards" />
          <Tab label="Locations" />
          <Tab label="Card History" />
        </Tabs>
        {tab === 0 && (
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>Your Cards</Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              {cards.map(card => (
                <Card key={card.id} sx={{ minWidth: 220, mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>{card.name || 'Unnamed Card'}</Typography>
                    <Typography variant="body2" color="text.secondary">UID: {card.uid}</Typography>
                    <Box sx={{ mt: 1 }}>
                      <IconButton size="small" onClick={() => { setSelectedCard(card); setRenameDialog(true); setRenameValue(card.name || ''); }}><EditIcon fontSize="small" /></IconButton>
                      <IconButton size="small" onClick={() => handleDeleteCard(card)}><DeleteIcon fontSize="small" /></IconButton>
                      <IconButton size="small" onClick={() => { setSelectedCard(card); setAssignDialog(true); }}><AddIcon fontSize="small" /></IconButton>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Box>
        )}
        {tab === 1 && (
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>Locations</Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField label="Location name" value={newLocation} onChange={e => setNewLocation(e.target.value)} />
              <TextField label="Description" value={newLocationDesc} onChange={e => setNewLocationDesc(e.target.value)} />
              <Button variant="contained" startIcon={<AddIcon />} onClick={handleAddLocation}>Add Location</Button>
            </Box>
            <List sx={{ mb: 3 }}>
              {locations.map(loc => (
                <ListItem key={loc.id} secondaryAction={
                  <IconButton edge="end" onClick={() => handleDeleteLocation(loc)}><DeleteIcon /></IconButton>
                }>
                  <ListItemText primary={loc.name} secondary={loc.description} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
        {tab === 2 && (
          <Box>
            <Typography variant="h6">Card History</Typography>
            <List>
              {cardHistory.map(hist => (
                <ListItem key={hist.id}>
                  <ListItemText
                    primary={`Card: ${hist.card_id} | Type: ${hist.card_type}`}
                    secondary={`First Seen: ${hist.first_seen} | Last Seen: ${hist.last_seen}`}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Container>
      {/* Rename Card Dialog */}
      <Dialog open={renameDialog} onClose={() => setRenameDialog(false)}>
        <DialogTitle>Rename Card</DialogTitle>
        <DialogContent>
          <TextField label="Card Name" value={renameValue} onChange={e => setRenameValue(e.target.value)} fullWidth />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRenameDialog(false)}>Cancel</Button>
          <Button onClick={handleRenameCard} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
      {/* Assign Card Dialog */}
      <Dialog open={assignDialog} onClose={() => setAssignDialog(false)}>
        <DialogTitle>Assign Card to Location</DialogTitle>
        <DialogContent>
          <FormControl fullWidth>
            <InputLabel>Location</InputLabel>
            <Select value={assignLocation} onChange={e => setAssignLocation(e.target.value)} label="Location">
              {locations.map(loc => (
                <MenuItem key={loc.id} value={loc.id}>{loc.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAssignDialog(false)}>Cancel</Button>
          <Button onClick={handleAssignCard} variant="contained">Assign</Button>
        </DialogActions>
      </Dialog>
      <Snackbar open={snackbar.open} autoHideDuration={3000} onClose={() => setSnackbar({ ...snackbar, open: false })}>
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  );
}

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (data?.user) setUser(data.user);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user || null);
    });
    return () => { listener?.subscription.unsubscribe(); };
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  if (!user) return <Auth onAuth={setUser} />;
  return <Dashboard user={user} onLogout={handleLogout} />;
}

export default App;
