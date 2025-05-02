import React, { useState } from 'react';
import { Box, Button, TextField, Typography, Paper, Link, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { supabase } from './supabaseClient';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const { error: loginError } = await supabase.auth.signInWithPassword({ email, password });
    if (loginError) {
      setError(loginError.message);
      setLoading(false);
      return;
    }
    setLoading(false);
    navigate('/dashboard');
  };

  return (
    <Container maxWidth="xs" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4, borderRadius: 3 }}>
        <Typography variant="h5" align="center" gutterBottom>Login to One</Typography>
        <form onSubmit={handleLogin}>
          <TextField label="Email" fullWidth margin="normal" value={email} onChange={e => setEmail(e.target.value)} />
          <TextField label="Password" type="password" fullWidth margin="normal" value={password} onChange={e => setPassword(e.target.value)} />
          {error && <Typography color="error" sx={{ mt: 1 }}>{error}</Typography>}
          <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }} disabled={loading}>{loading ? 'Logging in...' : 'Login'}</Button>
        </form>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
          <Link component="button" variant="body2" onClick={() => navigate('/signup')}>Sign Up</Link>
          <Link component="button" variant="body2" onClick={() => alert('Forgot password flow coming soon!')}>Forgot password?</Link>
        </Box>
      </Paper>
    </Container>
  );
} 