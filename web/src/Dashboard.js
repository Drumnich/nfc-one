import React, { useState } from 'react';
import { Box, Button, Typography, Paper, Container, List, ListItem, ListItemText, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, TextField } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';

export default function Dashboard() {
  const [addCardOpen, setAddCardOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState(null);
  // Placeholder data
  const cards = [];

  return (
    <Container maxWidth="md" sx={{ mt: 6 }}>
      <Paper sx={{ p: 4, borderRadius: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>My Cards</Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setAddCardOpen(true)}>Add Card</Button>
        </Box>
        <List>
          {cards.length === 0 && <Typography color="text.secondary">No cards yet. Click 'Add Card' to get started.</Typography>}
          {cards.map(card => (
            <ListItem key={card.id} button onClick={() => setSelectedCard(card)}>
              <ListItemText primary={card.name} secondary={`UID: ${card.uid}`} />
              <IconButton><EditIcon /></IconButton>
            </ListItem>
          ))}
        </List>
      </Paper>
      {/* Card Details Section */}
      {selectedCard && (
        <Paper sx={{ p: 4, borderRadius: 3 }}>
          <Typography variant="h6">Card Details</Typography>
          <Typography>Name: {selectedCard.name}</Typography>
          <Typography>UID: {selectedCard.uid}</Typography>
          <Typography sx={{ mt: 2, fontWeight: 600 }}>Locations</Typography>
          {/* List locations for this card here */}
        </Paper>
      )}
      {/* Add Card Modal */}
      <Dialog open={addCardOpen} onClose={() => setAddCardOpen(false)}>
        <DialogTitle>Add Card</DialogTitle>
        <DialogContent>
          {/* Scan card, enter name, assign location */}
          <Typography>Scan your card, then enter a name and assign a location.</Typography>
          <TextField label="Card Name" fullWidth sx={{ mt: 2 }} />
          <TextField label="Location" fullWidth sx={{ mt: 2 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddCardOpen(false)}>Cancel</Button>
          <Button variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
} 