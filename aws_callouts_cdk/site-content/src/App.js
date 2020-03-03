import React from 'react';
import Amplify, {graphqlOperation, API} from 'aws-amplify';
import * as queries from './graphql/queries'
import * as mutations from './graphql/mutations';
import * as subscriptions from './graphql/subscriptions';
import {Form, Field} from 'react-final-form'
import arrayMutators from 'final-form-arrays'
import {FieldArray} from 'react-final-form-arrays'
import {TextField, Select} from 'final-form-material-ui';
import moment from 'moment-timezone';
import LinkIcon from '@material-ui/icons/Link';
import {
    Typography,
    Paper,
    Grid,
    Button,
    CssBaseline,
    MenuItem,
    Divider,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow
} from '@material-ui/core';
import {Connect} from "aws-amplify-react";
import {makeStyles} from "@material-ui/styles";
import IconButton from "@material-ui/core/IconButton";

Amplify.configure({
    aws_appsync_graphqlEndpoint: process.env.REACT_APP_API_URL || 'https://6q2s5kzta5bgtpe3alizo2mnca.appsync-api.ap-southeast-2.amazonaws.com/graphql',
    aws_appsync_region: process.env.REACT_APP_REGION || 'ap-southeast-2',
    aws_appsync_authenticationType: 'AWS_IAM',
    Auth: {
        identityPoolId: process.env.REACT_APP_IDENTITY_POOL_ID || 'ap-southeast-2:a68923b4-fbfe-427d-b953-1bd63deeb7b6',
        region: process.env.REACT_APP_REGION || 'ap-southeast-2',
        userPoolId: process.env.REACT_APP_USER_POOL_ID || 'ap-southeast-2_v8Fn6hF63',
        userPoolWebClientId: process.env.REACT_APP_USER_POOL_WEB_CLIENT_ID || '55cg2mva30n9fi89d69tltlfem'
    }
});

const onSubmit = async task => {
    task.receivers = task.receivers.map((v, i) => {
        v.id = `${task.task_id}_${i + 1}`;
        v.receiver_id = `${i + 1}`;
        return v
    });
    console.log(task);
    const createCallTask = await API.graphql(graphqlOperation(mutations.createCallTask, {task}));
    console.log(createCallTask);
};

const initialValues = {
    "task_id": `WeBorrowCallDemo${moment().unix()}`,
    "greeting": "Hi {{ username }}. This is a survey from We Borrow for collecting review about our lending services.",
    "ending": "Good Bye {{ username }} and have a nice day!",
    "questions": [
        {
            "question_template": "How much loan did you apply for?",
            "question_type": "NUMBER"
        },
        {
            "question_template": "Is this the first time you apply for the loan?",
            "question_type": "YES_NO"
        },
        {
            "question_template": "For the further follow-up, we like to call you back. Which date do you prefer?",
            "question_type": "DATE"
        },
        {
            "question_template": "Preferred call back time?",
            "question_type": "TIME"
        },
        {
            "question_template": "How do you know We Borrow? A. Newsletter, B. Social Media, C. Promotion, D. Ads, or E. From Friend.",
            "question_type": "MULTIPLE_CHOICE"
        },
        {
            "question_template": "To complete the survey, please say OK.",
            "question_type": "OK"
        }
    ]
};

const useStyles = makeStyles(() => ({
    root: {
        flexGrow: 1
    },
    paper: {
        padding: 12
    },
    question: {
        marginTop: 10,
        marginBottom: 10,
        marginLeft: 20,
        marginRight: 20,
        padding: 8
    }
}));

function App() {
    const classes = useStyles();
    return (
        // <div style={{ padding: 16, margin: 'auto', maxWidth: 600 }}>
        <div style={{padding: 16}}>
            <Grid container spacing={4} className={classes.root}>
                <Grid item xs={6}>
                    <CssBaseline/>
                    <Form
                        onSubmit={onSubmit}
                        initialValues={initialValues}
                        mutators={{
                            ...arrayMutators
                        }}
                        render={({handleSubmit, form: {mutators: {push, pop}}, reset, submitting, pristine, values, form}) => (
                            <form onSubmit={handleSubmit} noValidate>
                                <Paper style={{padding: 16}}>
                                    <Grid container alignItems="flex-start" spacing={2}>
                                        <Grid item xs={12}>
                                            <Field
                                                name="task_id"
                                                fullWidth
                                                required
                                                component={TextField}
                                                type="text"
                                                label="Task ID"
                                            />
                                        </Grid>
                                        <Grid item xs={12}>
                                            <Field
                                                fullWidth
                                                required
                                                name="greeting"
                                                component={TextField}
                                                type="text"
                                                label="Greeting"
                                            />
                                        </Grid>
                                        <Grid item xs={12}>
                                            <Field
                                                fullWidth
                                                required
                                                name="ending"
                                                component={TextField}
                                                type="text"
                                                label="Ending"
                                            />
                                        </Grid>

                                        <Grid container><Grid item xs={12}><Divider
                                            style={{marginTop: 20, marginBottom: 20}}/></Grid></Grid>

                                        <Grid container>
                                            <Grid item xs={6}>
                                                <Button variant="contained" color="primary"
                                                        onClick={() => push('questions', undefined)} fullWidth>Add
                                                    Question</Button>
                                            </Grid>
                                            <Grid item xs={6}>
                                                <Button variant="contained" color="secondary"
                                                        onClick={() => pop('questions')}
                                                        fullWidth>Remove Question</Button>
                                            </Grid>
                                        </Grid>
                                        <Grid container spacing={2}>
                                            <FieldArray name="questions">
                                                {({fields}) =>
                                                    fields.map((name, index) => (
                                                        <Paper key={index} className={classes.question} component={Grid}
                                                               elevation={6} container item
                                                               spacing={1}>
                                                            <Grid item xs={12}>
                                                                <Field
                                                                    name={`${name}.question_template`}
                                                                    component={TextField}
                                                                    type="text"
                                                                    label="Question Template"
                                                                    fullWidth
                                                                    required
                                                                />
                                                            </Grid>
                                                            <Grid item xs={12}>
                                                                <Field
                                                                    name={`${name}.question_type`}
                                                                    component={Select}
                                                                    label="Question Type"
                                                                    fullWidth
                                                                    required
                                                                    formControlProps={{fullWidth: true}}
                                                                >
                                                                    <MenuItem value="YES_NO">Yes/No</MenuItem>
                                                                    <MenuItem value="MULTIPLE_CHOICE">Multiple
                                                                        Choice</MenuItem>
                                                                    <MenuItem value="NUMBER">Number</MenuItem>
                                                                    <MenuItem value="DATE">Date</MenuItem>
                                                                    <MenuItem value="TIME">Time</MenuItem>
                                                                    <MenuItem value="OK">OK</MenuItem>
                                                                </Field>
                                                            </Grid>
                                                            <Grid item xs={12} style={{marginBottom: 8}}>
                                                                <Button fullWidth variant="outlined"
                                                                        color="secondary"
                                                                        size="large"
                                                                        onClick={() => fields.remove(index)}>REMOVE</Button>
                                                            </Grid>
                                                        </Paper>
                                                    ))
                                                }
                                            </FieldArray>
                                        </Grid>

                                        <Grid container><Grid item xs={12}><Divider
                                            style={{marginTop: 20, marginBottom: 20}}/></Grid></Grid>

                                        <Grid container>
                                            <Grid item xs={6}>
                                                <Button variant="contained" color="primary"
                                                        onClick={() => push('receivers', undefined)} fullWidth>Add
                                                    Receiver</Button>
                                            </Grid>
                                            <Grid item xs={6}>
                                                <Button variant="contained" color="secondary"
                                                        onClick={() => pop('receivers')}
                                                        fullWidth>Remove Receiver</Button>
                                            </Grid>
                                        </Grid>
                                        <Grid container>
                                            <FieldArray name="receivers">
                                                {({fields}) =>
                                                    fields.map((name, index) => (
                                                        <Paper key={index} className={classes.question} component={Grid}
                                                               elevation={6} container item
                                                               spacing={1}>
                                                            <Grid item xs={12}>
                                                                <Field
                                                                    name={`${name}.phone_number`}
                                                                    component={TextField}
                                                                    type="text"
                                                                    label="Phone Number"
                                                                    required
                                                                    fullWidth
                                                                />
                                                            </Grid>
                                                            <Grid item xs={12}>
                                                                <Field
                                                                    name={`${name}.username`}
                                                                    component={TextField}
                                                                    type="text"
                                                                    label="Name"
                                                                    required
                                                                    fullWidth
                                                                />
                                                            </Grid>
                                                            <Grid item xs={12}>
                                                                <Button variant="outlined" color="secondary"
                                                                        size="large"
                                                                        onClick={() => fields.remove(index)} fullWidth
                                                                        style={{marginBottom: 8}}>REMOVE</Button>
                                                            </Grid>
                                                        </Paper>
                                                    ))
                                                }
                                            </FieldArray>
                                        </Grid>

                                        <Grid container><Grid item xs={12}><Divider
                                            style={{marginTop: 20, marginBottom: 20}}/></Grid></Grid>

                                        <Grid item style={{marginTop: 16}}>
                                            <Button
                                                type="button"
                                                variant="contained"
                                                onClick={reset}
                                                disabled={submitting || pristine}
                                            >
                                                Reset
                                            </Button>
                                        </Grid>
                                        <Grid item style={{marginTop: 16}}>
                                            <Button
                                                variant="contained"
                                                color="primary"
                                                type="submit"
                                                disabled={submitting}
                                            >
                                                Submit
                                            </Button>
                                        </Grid>
                                    </Grid>
                                </Paper>
                                {/*<pre>{JSON.stringify(values, 0, 2)}</pre>*/}
                            </form>
                        )}
                    />
                </Grid>
                <Grid item xs={6}>
                    <Grid container spacing={2}>
                        <Grid item xs={12}>
                            <Paper className={classes.paper}>
                                <Typography variant="h5">Call Task Record</Typography>
                                <Divider style={{marginTop: 4, marginBottom: 8}}/>
                                <TableContainer component={Paper}>
                                    <Table className={classes.table} size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Task ID</TableCell>
                                                <TableCell>Created At</TableCell>
                                                <TableCell>Number of Question</TableCell>
                                                <TableCell>Number of Receiver</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            <Connect
                                                query={graphqlOperation(queries.getLatestCallTaskRecords, {
                                                    limit: 10,
                                                })}
                                                subscription={graphqlOperation(subscriptions.createCallTask)}
                                                onSubscriptionMsg={({getLatestCallTaskRecords}, {createCallTask}) => {
                                                    getLatestCallTaskRecords.unshift(createCallTask);
                                                    if (getLatestCallTaskRecords.length > 10) getLatestCallTaskRecords.pop();
                                                    return {getLatestCallTaskRecords};
                                                }}
                                            >
                                                {({data: {getLatestCallTaskRecords}, loading, errors}) => {
                                                    if (errors && errors.length) console.log(errors);
                                                    if (loading || !getLatestCallTaskRecords) return (
                                                        <TableRow><TableCell>Loading</TableCell></TableRow>);
                                                    return getLatestCallTaskRecords.map((record, i) => (
                                                        <TableRow key={`${record.task_id + i}}`}>
                                                            <TableCell>{record.task_id}</TableCell>
                                                            <TableCell>{moment.unix(record.created_at).fromNow()}</TableCell>
                                                            <TableCell>{record.questions.length}</TableCell>
                                                            <TableCell>{record.receivers.length}</TableCell>
                                                        </TableRow>
                                                    ))
                                                }}
                                            </Connect>
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </Paper>
                        </Grid>
                        <Grid item xs={12}>
                            <Paper className={classes.paper}>
                                <Typography variant="h5">Call Report Record</Typography>
                                <Divider style={{marginTop: 4, marginBottom: 8}}/>
                                <TableContainer component={Paper}>
                                    <Table className={classes.table} size="small">
                                        <TableHead>
                                            <TableRow>
                                                <TableCell>Task ID</TableCell>
                                                <TableCell>Created At</TableCell>
                                                <TableCell>Report Download</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            <Connect
                                                query={graphqlOperation(queries.getLatestCallReportRecords, {
                                                    limit: 10,
                                                })}
                                                subscription={graphqlOperation(subscriptions.createCallReport)}
                                                onSubscriptionMsg={({getLatestCallReportRecords}, {createCallReport}) => {
                                                    getLatestCallReportRecords.unshift(createCallReport);
                                                    if (getLatestCallReportRecords.length > 10) getLatestCallReportRecords.pop();
                                                    return {getLatestCallReportRecords};
                                                }}
                                            >
                                                {({data: {getLatestCallReportRecords}, loading, errors}) => {
                                                    if (errors && errors.length) console.log(errors);
                                                    if (loading || !getLatestCallReportRecords) return (
                                                        <TableRow><TableCell>Loading</TableCell></TableRow>);
                                                    return getLatestCallReportRecords.map((record, i) => (
                                                        <TableRow key={`${record.task_id + i}}`}>
                                                            <TableCell>{record.task_id}</TableCell>
                                                            <TableCell>{moment.unix(record.created_at).fromNow()}</TableCell>
                                                            <TableCell><IconButton size="small" aria-label="link"
                                                                                   color="primary"
                                                                                   href={record.presigned_url}><LinkIcon/></IconButton></TableCell>
                                                        </TableRow>
                                                    ))
                                                }}
                                            </Connect>
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </Paper>
                        </Grid>
                    </Grid>
                </Grid>
            </Grid>
        </div>
    );
}

export default App;
