import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Tabs,
  Tab,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Chip,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  AccessTime as AccessTimeIcon,
} from '@mui/icons-material';
import { supabase } from '../supabaseClient';

function CorporateDashboard() {
  const [tab, setTab] = useState(0);
  const [buildings, setBuildings] = useState([]);
  const [users, setUsers] = useState([]);
  const [accessPoints, setAccessPoints] = useState([]);
  const [cards, setCards] = useState([]);
  const [accessLogs, setAccessLogs] = useState([]);
  const [openBuildingDialog, setOpenBuildingDialog] = useState(false);
  const [openUserDialog, setOpenUserDialog] = useState(false);
  const [openAccessPointDialog, setOpenAccessPointDialog] = useState(false);
  const [openCardAccessDialog, setOpenCardAccessDialog] = useState(false);
  const [newBuilding, setNewBuilding] = useState({ name: '', address: '', description: '' });
  const [newUser, setNewUser] = useState({ email: '', name: '', role: 'building_admin' });
  const [newAccessPoint, setNewAccessPoint] = useState({ name: '', description: '', access_level: 1 });
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [selectedCard, setSelectedCard] = useState(null);
  const [cardAccess, setCardAccess] = useState({});

  useEffect(() => {
    fetchBuildings();
    fetchUsers();
    fetchAccessPoints();
    fetchCards();
    fetchAccessLogs();
  }, []);

  const fetchBuildings = async () => {
    const { data, error } = await supabase
      .from('buildings')
      .select('*')
      .order('created_at', { ascending: false });
    
    if (error) {
      console.error('Error fetching buildings:', error);
      return;
    }
    setBuildings(data);
  };

  const fetchUsers = async () => {
    const { data, error } = await supabase
      .from('users')
      .select('*, building_admins(building_id)')
      .eq('user_type', 'building_admin');
    
    if (error) {
      console.error('Error fetching users:', error);
      return;
    }
    setUsers(data);
  };

  const fetchAccessPoints = async () => {
    const { data, error } = await supabase
      .from('access_points')
      .select('*, buildings(name)')
      .order('created_at', { ascending: false });
    
    if (error) {
      console.error('Error fetching access points:', error);
      return;
    }
    setAccessPoints(data);
  };

  const fetchCards = async () => {
    const { data, error } = await supabase
      .from('cards')
      .select('*, users(email), card_access(access_point_id, access_level, schedule_start, schedule_end, days_of_week)')
      .order('created_at', { ascending: false });
    
    if (error) {
      console.error('Error fetching cards:', error);
      return;
    }
    setCards(data);
  };

  const fetchAccessLogs = async () => {
    const { data, error } = await supabase
      .from('access_logs')
      .select('*, cards(card_uid, users(email)), access_points(name, buildings(name))')
      .order('timestamp', { ascending: false })
      .limit(100);
    
    if (error) {
      console.error('Error fetching access logs:', error);
      return;
    }
    setAccessLogs(data);
  };

  const handleAddBuilding = async () => {
    const { data, error } = await supabase
      .from('buildings')
      .insert([newBuilding])
      .select();
    
    if (error) {
      console.error('Error adding building:', error);
      return;
    }
    
    setBuildings([...buildings, data[0]]);
    setOpenBuildingDialog(false);
    setNewBuilding({ name: '', address: '', description: '' });
  };

  const handleAddUser = async () => {
    // First create the user
    const { data: userData, error: userError } = await supabase.auth.signUp({
      email: newUser.email,
      password: 'temporary123', // This should be changed by the user
    });

    if (userError) {
      console.error('Error creating user:', userError);
      return;
    }

    // Then add them as a building admin
    const { error: adminError } = await supabase
      .from('building_admins')
      .insert([{
        building_id: selectedBuilding.id,
        user_id: userData.user.id
      }]);

    if (adminError) {
      console.error('Error adding building admin:', adminError);
      return;
    }

    setOpenUserDialog(false);
    setNewUser({ email: '', name: '', role: 'building_admin' });
    fetchUsers();
  };

  const handleAddAccessPoint = async () => {
    const { data, error } = await supabase
      .from('access_points')
      .insert([{
        ...newAccessPoint,
        building_id: selectedBuilding.id
      }])
      .select();
    
    if (error) {
      console.error('Error adding access point:', error);
      return;
    }
    
    setAccessPoints([...accessPoints, data[0]]);
    setOpenAccessPointDialog(false);
    setNewAccessPoint({ name: '', description: '', access_level: 1 });
  };

  const handleUpdateCardAccess = async () => {
    const { error } = await supabase
      .from('card_access')
      .upsert([{
        card_id: selectedCard.id,
        access_point_id: cardAccess.access_point_id,
        access_level: cardAccess.access_level,
        schedule_start: cardAccess.schedule_start,
        schedule_end: cardAccess.schedule_end,
        days_of_week: cardAccess.days_of_week
      }]);

    if (error) {
      console.error('Error updating card access:', error);
      return;
    }

    setOpenCardAccessDialog(false);
    fetchCards();
  };

  const handleRevokeAccess = async (cardId) => {
    const { error } = await supabase
      .from('cards')
      .update({ status: 'revoked' })
      .eq('id', cardId);

    if (error) {
      console.error('Error revoking access:', error);
      return;
    }

    fetchCards();
  };

  const handleRestoreAccess = async (cardId) => {
    const { error } = await supabase
      .from('cards')
      .update({ status: 'active' })
      .eq('id', cardId);

    if (error) {
      console.error('Error restoring access:', error);
      return;
    }

    fetchCards();
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tab} onChange={(e, newValue) => setTab(newValue)}>
                <Tab label="Buildings" />
                <Tab label="Access Points" />
                <Tab label="Cards" />
                <Tab label="Users" />
                <Tab label="Access Logs" />
              </Tabs>
            </Box>

            {/* Buildings Tab */}
            {tab === 0 && (
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">Buildings</Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenBuildingDialog(true)}
                  >
                    Add Building
                  </Button>
                </Box>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Address</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {buildings.map((building) => (
                        <TableRow key={building.id}>
                          <TableCell>{building.name}</TableCell>
                          <TableCell>{building.address}</TableCell>
                          <TableCell>{building.description}</TableCell>
                          <TableCell>
                            <IconButton onClick={() => setSelectedBuilding(building)}>
                              <EditIcon />
                            </IconButton>
                            <IconButton>
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {/* Access Points Tab */}
            {tab === 1 && (
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">Access Points</Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenAccessPointDialog(true)}
                    disabled={!selectedBuilding}
                  >
                    Add Access Point
                  </Button>
                </Box>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Building</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Description</TableCell>
                        <TableCell>Access Level</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {accessPoints.map((point) => (
                        <TableRow key={point.id}>
                          <TableCell>{point.buildings?.name}</TableCell>
                          <TableCell>{point.name}</TableCell>
                          <TableCell>{point.description}</TableCell>
                          <TableCell>{point.access_level}</TableCell>
                          <TableCell>
                            <IconButton>
                              <EditIcon />
                            </IconButton>
                            <IconButton>
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {/* Cards Tab */}
            {tab === 2 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>Cards</Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Card UID</TableCell>
                        <TableCell>User</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Access Points</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {cards.map((card) => (
                        <TableRow key={card.id}>
                          <TableCell>{card.card_uid}</TableCell>
                          <TableCell>{card.users?.email}</TableCell>
                          <TableCell>{card.name}</TableCell>
                          <TableCell>
                            <Chip
                              label={card.status}
                              color={card.status === 'active' ? 'success' : 'error'}
                            />
                          </TableCell>
                          <TableCell>
                            {card.card_access?.length || 0} points
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedCard(card);
                                setCardAccess({});
                                setOpenCardAccessDialog(true);
                              }}
                            >
                              <AccessTimeIcon />
                            </IconButton>
                          </TableCell>
                          <TableCell>
                            {card.status === 'revoked' ? (
                              <IconButton onClick={() => handleRestoreAccess(card.id)}>
                                <CheckCircleIcon />
                              </IconButton>
                            ) : (
                              <IconButton onClick={() => handleRevokeAccess(card.id)}>
                                <BlockIcon />
                              </IconButton>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {/* Users Tab */}
            {tab === 3 && (
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">Building Users</Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenUserDialog(true)}
                  >
                    Add User
                  </Button>
                </Box>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Email</TableCell>
                        <TableCell>Building</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {users.map((user) => (
                        <TableRow key={user.id}>
                          <TableCell>{user.username}</TableCell>
                          <TableCell>{user.email}</TableCell>
                          <TableCell>
                            {buildings.find(b => b.id === user.building_admins[0]?.building_id)?.name}
                          </TableCell>
                          <TableCell>
                            <IconButton>
                              <EditIcon />
                            </IconButton>
                            <IconButton>
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {/* Access Logs Tab */}
            {tab === 4 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>Recent Access Logs</Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Timestamp</TableCell>
                        <TableCell>Card UID</TableCell>
                        <TableCell>User</TableCell>
                        <TableCell>Building</TableCell>
                        <TableCell>Access Point</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {accessLogs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                          <TableCell>{log.cards?.card_uid}</TableCell>
                          <TableCell>{log.cards?.users?.email}</TableCell>
                          <TableCell>{log.access_points?.buildings?.name}</TableCell>
                          <TableCell>{log.access_points?.name}</TableCell>
                          <TableCell>
                            <Chip
                              label={log.access_granted ? 'Granted' : 'Denied'}
                              color={log.access_granted ? 'success' : 'error'}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Add Building Dialog */}
      <Dialog open={openBuildingDialog} onClose={() => setOpenBuildingDialog(false)}>
        <DialogTitle>Add New Building</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Building Name"
            fullWidth
            value={newBuilding.name}
            onChange={(e) => setNewBuilding({ ...newBuilding, name: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Address"
            fullWidth
            value={newBuilding.address}
            onChange={(e) => setNewBuilding({ ...newBuilding, address: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={4}
            value={newBuilding.description}
            onChange={(e) => setNewBuilding({ ...newBuilding, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenBuildingDialog(false)}>Cancel</Button>
          <Button onClick={handleAddBuilding} variant="contained">Add</Button>
        </DialogActions>
      </Dialog>

      {/* Add User Dialog */}
      <Dialog open={openUserDialog} onClose={() => setOpenUserDialog(false)}>
        <DialogTitle>Add New User</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Email"
            type="email"
            fullWidth
            value={newUser.email}
            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Name"
            fullWidth
            value={newUser.name}
            onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel>Building</InputLabel>
            <Select
              value={selectedBuilding?.id || ''}
              onChange={(e) => setSelectedBuilding(buildings.find(b => b.id === e.target.value))}
              label="Building"
            >
              {buildings.map((building) => (
                <MenuItem key={building.id} value={building.id}>
                  {building.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenUserDialog(false)}>Cancel</Button>
          <Button onClick={handleAddUser} variant="contained">Add</Button>
        </DialogActions>
      </Dialog>

      {/* Add Access Point Dialog */}
      <Dialog open={openAccessPointDialog} onClose={() => setOpenAccessPointDialog(false)}>
        <DialogTitle>Add New Access Point</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Name"
            fullWidth
            value={newAccessPoint.name}
            onChange={(e) => setNewAccessPoint({ ...newAccessPoint, name: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            value={newAccessPoint.description}
            onChange={(e) => setNewAccessPoint({ ...newAccessPoint, description: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Access Level"
            type="number"
            fullWidth
            value={newAccessPoint.access_level}
            onChange={(e) => setNewAccessPoint({ ...newAccessPoint, access_level: parseInt(e.target.value) })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAccessPointDialog(false)}>Cancel</Button>
          <Button onClick={handleAddAccessPoint} variant="contained">Add</Button>
        </DialogActions>
      </Dialog>

      {/* Card Access Dialog */}
      <Dialog open={openCardAccessDialog} onClose={() => setOpenCardAccessDialog(false)}>
        <DialogTitle>Manage Card Access</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Access Point</InputLabel>
            <Select
              value={cardAccess.access_point_id || ''}
              onChange={(e) => setCardAccess({ ...cardAccess, access_point_id: e.target.value })}
              label="Access Point"
            >
              {accessPoints.map((point) => (
                <MenuItem key={point.id} value={point.id}>
                  {point.buildings?.name} - {point.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            margin="dense"
            label="Access Level"
            type="number"
            fullWidth
            value={cardAccess.access_level || 1}
            onChange={(e) => setCardAccess({ ...cardAccess, access_level: parseInt(e.target.value) })}
          />
          <TextField
            margin="dense"
            label="Schedule Start"
            type="time"
            fullWidth
            value={cardAccess.schedule_start || ''}
            onChange={(e) => setCardAccess({ ...cardAccess, schedule_start: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            margin="dense"
            label="Schedule End"
            type="time"
            fullWidth
            value={cardAccess.schedule_end || ''}
            onChange={(e) => setCardAccess({ ...cardAccess, schedule_end: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2">Days of Week</Typography>
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, index) => (
              <FormControlLabel
                key={day}
                control={
                  <Switch
                    checked={cardAccess.days_of_week?.includes(index) || false}
                    onChange={(e) => {
                      const days = cardAccess.days_of_week || [];
                      if (e.target.checked) {
                        setCardAccess({ ...cardAccess, days_of_week: [...days, index] });
                      } else {
                        setCardAccess({ ...cardAccess, days_of_week: days.filter(d => d !== index) });
                      }
                    }}
                  />
                }
                label={day}
              />
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCardAccessDialog(false)}>Cancel</Button>
          <Button onClick={handleUpdateCardAccess} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default CorporateDashboard; 