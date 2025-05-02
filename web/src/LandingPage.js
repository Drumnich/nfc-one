import React from 'react';
import { Box, Typography, Button, Container, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();
  return (
    <Container maxWidth="md" sx={{ mt: 10 }}>
      <Paper elevation={3} sx={{ p: 6, borderRadius: 4, textAlign: 'center', background: 'linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%)', color: '#fff' }}>
        <Typography variant="h2" sx={{ fontWeight: 700, mb: 2, letterSpacing: 2 }}>One</Typography>
        <Typography variant="h5" sx={{ mb: 4 }}>
          One is your universal access pass. Manage all your doors, lounges, and gates with a single card and a single app. Secure, simple, and always in your pocket.
        </Typography>
        <Button variant="contained" size="large" sx={{ fontWeight: 600, fontSize: 20, px: 6, py: 2, borderRadius: 3, background: '#fff', color: '#3a47d5', '&:hover': { background: '#e3e3e3' } }} onClick={() => navigate('/login')}>Get Started</Button>
      </Paper>
    </Container>
  );
} 